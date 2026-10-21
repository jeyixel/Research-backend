"""Creator-disjoint research experiments. These artifacts never enable API predictions."""

import time

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, brier_score_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from .config import Settings
from .data import write_json
from .features import TITLE_COLUMNS, VISUAL_COLUMNS, title_features
from .pipeline import load_features

EXPERIMENTS = ("prior", "visual", "title_category", "clip", "combined")


def predictive_inputs(frame, features, embeddings):
    # Construct an allowlist rather than selecting all non-label columns.
    # channel_id/fold/age/history/outcomes never reach an estimator.
    result = pd.DataFrame({"title": frame.title.tolist(), "category": frame.category.tolist()})
    for key in VISUAL_COLUMNS:
        result[key] = pd.to_numeric(features[key], errors="coerce").to_numpy()
    for key in TITLE_COLUMNS:
        result[key] = [title_features(title)[key] for title in result.title]
    clip = pd.DataFrame(embeddings, columns=[f"clip_{i}" for i in range(embeddings.shape[1])])
    return pd.concat([result, clip], axis=1)


def purged_split(frame: pd.DataFrame, test_fold: int, development_only=False):
    test = frame.fold == test_fold
    candidates = frame.fold != test_fold
    if development_only:
        candidates &= frame.fold != 4
    duplicate_groups = set(frame.loc[test, "duplicate_group"])
    train = candidates & ~frame.duplicate_group.isin(duplicate_groups)
    if set(frame.loc[train, "channel_id"]) & set(frame.loc[test, "channel_id"]):
        raise ValueError("Channel leakage detected.")
    if set(frame.loc[train, "duplicate_group"]) & duplicate_groups:
        raise ValueError("Duplicate leakage detected.")
    return np.flatnonzero(train), np.flatnonzero(test)


def model_pipeline(experiment: str, regularization: float, embedding_dim: int):
    if experiment == "prior":
        return DummyClassifier(strategy="prior")
    branches = []
    numeric = []
    if experiment in ("visual", "combined"):
        numeric.extend(VISUAL_COLUMNS)
    if experiment in ("title_category", "combined"):
        numeric.extend(TITLE_COLUMNS)
        branches.extend(
            [
                (
                    "title",
                    TfidfVectorizer(
                        analyzer="char_wb", ngram_range=(2, 4), min_df=2, max_features=2000, sublinear_tf=True
                    ),
                    "title",
                ),
                ("category", OneHotEncoder(handle_unknown="ignore"), ["category"]),
            ]
        )
    if experiment in ("clip", "combined"):
        numeric.extend(f"clip_{i}" for i in range(embedding_dim))
    branches.append(
        (
            "numeric",
            Pipeline(
                [
                    (
                        "impute",
                        SimpleImputer(strategy="median", add_indicator=True, keep_empty_features=True),
                    ),
                    ("scale", StandardScaler()),
                ]
            ),
            numeric,
        )
    )
    return Pipeline(
        [
            ("features", ColumnTransformer(branches, remainder="drop", sparse_threshold=0.8)),
            (
                "classifier",
                LogisticRegression(C=regularization, solver="liblinear", max_iter=500, random_state=42),
            ),
        ]
    )


def metrics(y, probability, weights=None):
    y, probability = np.asarray(y), np.asarray(probability)
    if len(y) == 0:
        return {"n": 0, "auroc": None, "balanced_accuracy": None, "brier": None}
    two_classes = len(np.unique(y)) == 2
    return {
        "n": len(y),
        "positive_fraction": round(float(np.average(y, weights=weights)), 6),
        "auroc": round(float(roc_auc_score(y, probability, sample_weight=weights)), 6)
        if two_classes
        else None,
        "balanced_accuracy": round(
            float(balanced_accuracy_score(y, probability >= 0.5, sample_weight=weights)), 6
        )
        if two_classes
        else None,
        "brier": round(float(brier_score_loss(y, probability, sample_weight=weights)), 6),
    }


def channel_weights(channels):
    values = pd.Series(np.asarray(channels))
    return (1.0 / values.map(values.value_counts())).to_numpy()


def bootstrap(y, probability, channels, repetitions=200, other=None):
    generator = np.random.default_rng(42)
    unique, inverse = np.unique(channels, return_inverse=True)
    values, differences = [], []
    for _ in range(repetitions):
        samples = generator.integers(0, len(unique), size=len(unique))
        weights = np.bincount(samples, minlength=len(unique))[inverse].astype(float)
        if len(np.unique(np.asarray(y)[weights > 0])) < 2:
            continue
        auc = roc_auc_score(y, probability, sample_weight=weights)
        values.append(auc)
        if other is not None:
            differences.append(auc - roc_auc_score(y, other, sample_weight=weights))

    def interval(items):
        return [round(float(q), 6) for q in np.quantile(items, [0.025, 0.975])] if items else None

    return {
        "channel_resamples": repetitions,
        "auroc_95_percent_interval": interval(values),
        "paired_auroc_difference_95_percent_interval": interval(differences),
    }


def run_evaluation(settings: Settings, target="y_rel_neighbors", repetitions=200):
    started = time.monotonic()
    frame, features, embeddings, metadata = load_features(settings)
    if target not in ("y_rel_neighbors", "y_rel_prev"):
        raise ValueError("Unsupported research target.")
    values = pd.to_numeric(frame[target], errors="coerce")
    keep = values.notna().to_numpy()
    frame = frame.loc[keep].reset_index(drop=True)
    features = features.loc[keep].reset_index(drop=True)
    embeddings = embeddings[keep]
    y = (values[keep].to_numpy() > 0).astype(int)
    inputs = predictive_inputs(frame, features, embeddings)
    train, test = purged_split(frame, 4)
    if not len(train) or not len(test) or len(np.unique(y[train])) < 2 or len(np.unique(y[test])) < 2:
        raise ValueError("Insufficient class coverage after fold/duplicate purging.")
    # Select models without opening final-test outcomes or using their features in preprocessing.
    selections, development_predictions = {}, {}
    final_groups = set(frame.loc[frame.fold == 4, "duplicate_group"])
    clean_development = ((frame.fold != 4) & ~frame.duplicate_group.isin(final_groups)).to_numpy()
    for experiment in EXPERIMENTS:
        candidates = []
        for c_value in [1.0] if experiment == "prior" else [0.1, 1.0, 10.0]:
            scores, oof = [], np.full(len(frame), np.nan)
            for fold in range(4):
                tr, va = purged_split(frame, fold, development_only=True)
                # Test-related copies must not influence hyperparameters via validation either.
                tr = tr[clean_development[tr]]
                va = va[clean_development[va]]
                if not len(tr) or not len(va) or len(np.unique(y[tr])) < 2:
                    raise ValueError(f"Insufficient data for development fold {fold}.")
                estimator = model_pipeline(experiment, c_value, embeddings.shape[1])
                estimator.fit(inputs.iloc[tr], y[tr])
                probability = estimator.predict_proba(inputs.iloc[va])[:, 1]
                oof[va] = probability
                category_aucs = []
                for category in frame.iloc[va].category.unique():
                    mask = (frame.iloc[va].category == category).to_numpy()
                    score = metrics(y[va][mask], probability[mask])["auroc"]
                    if score is not None:
                        category_aucs.append(score)
                if category_aucs:
                    scores.append(float(np.mean(category_aucs)))
            candidates.append({"c": c_value, "development_macro_auroc": float(np.mean(scores)), "oof": oof})
            print(f"{experiment} C={c_value}: development macro AUROC {np.mean(scores):.4f}", flush=True)
        best = max(candidates, key=lambda item: item["development_macro_auroc"])
        selections[experiment] = {k: v for k, v in best.items() if k != "oof"}
        selections[experiment]["development_grid"] = [
            {key: value for key, value in candidate.items() if key != "oof"} for candidate in candidates
        ]
        development_predictions[experiment] = best["oof"]

    results, predictions = {}, {}
    target_dir = settings.artifact_dir / "research" / target
    target_dir.mkdir(parents=True, exist_ok=True)
    for experiment in EXPERIMENTS:
        c_value = selections[experiment]["c"]
        estimator = model_pipeline(experiment, c_value, embeddings.shape[1])
        estimator.fit(inputs.iloc[train], y[train])
        probability = estimator.predict_proba(inputs.iloc[test])[:, 1]
        predictions[experiment] = probability
        held = frame.iloc[test]
        slices = {}
        for column in ("category", "title_script"):
            if column in held:
                slices[column] = {
                    str(value): metrics(y[test][mask.to_numpy()], probability[mask.to_numpy()])
                    for value in held[column].unique()
                    for mask in [held[column] == value]
                }
        results[experiment] = {
            "selection": selections[experiment],
            "test": metrics(y[test], probability),
            "channel_balanced_test": metrics(y[test], probability, channel_weights(held.channel_id)),
            "slices": slices,
            "uncertainty": bootstrap(y[test], probability, held.channel_id.to_numpy(), repetitions),
        }
        joblib.dump(
            {
                "estimator": estimator,
                "target": target,
                "cache_key": metadata["cache_key"],
                "research_only": True,
                "allowed_inputs": list(inputs.columns),
            },
            target_dir / f"{experiment}.joblib",
        )
        print(f"{experiment}: held-out AUROC {results[experiment]['test']['auroc']}", flush=True)

    study = {
        "data_version": metadata["table_sha256"],
        "feature_version": metadata["cache_key"],
        "target": f"{target} > 0",
        "research_only": True,
        "final_test_fold": 4,
        "train_rows": len(train),
        "test_rows": len(test),
        "train_channels": frame.iloc[train].channel_id.nunique(),
        "test_channels": frame.iloc[test].channel_id.nunique(),
        "purged_development_rows": int((frame.fold != 4).sum()) - len(train),
        "results": results,
        "visual_increment_over_title": bootstrap(
            y[test],
            predictions["combined"],
            frame.iloc[test].channel_id.to_numpy(),
            repetitions,
            other=predictions["title_category"],
        ),
        "limitations": [
            "Retrospective public-view proxy, not CTR or redesign uplift.",
            "Collection-time outcomes have unequal ages; edited historical packaging is unknown.",
            "Character TF-IDF is a limited topic baseline; visual gain does not isolate design quality.",
            "Language slices are scripts, not verified languages.",
            "The final test must not be repeatedly used to tune the implementation.",
        ],
        "seconds": round(time.monotonic() - started, 2),
    }
    write_json(target_dir / "evaluation.json", study)
    out = frame.iloc[test][["video_id", "channel_id", "category", "title_script"]].copy()
    out["target"] = y[test]
    for experiment, prediction in predictions.items():
        out[experiment] = prediction
    out.to_csv(target_dir / "test_predictions.csv", index=False)
    oof = frame.loc[frame.fold != 4, ["video_id", "channel_id", "category", "fold"]].copy()
    oof["used_for_model_selection"] = clean_development[frame.fold != 4]
    oof["target"] = y[frame.fold != 4]
    for experiment, prediction in development_predictions.items():
        oof[experiment] = prediction[frame.fold != 4]
    oof.to_csv(target_dir / "development_predictions.csv", index=False)
    lines = [
        "# Module C held-out research results",
        "",
        f"Target: `{target} > 0`; final test fold: 4.",
        "",
        "| Experiment | AUROC | Balanced accuracy | Brier |",
        "|---|---:|---:|---:|",
    ]
    for name, item in results.items():
        item = item["test"]
        lines.append(f"| {name} | {item['auroc']} | {item['balanced_accuracy']} | {item['brier']} |")
    lines.extend(
        [
            "",
            "Paired combined-minus-title AUROC interval: "
            + str(study["visual_increment_over_title"]["paired_auroc_difference_95_percent_interval"]),
            "",
            *[f"- {text}" for text in study["limitations"]],
        ]
    )
    (target_dir / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")
    return study
