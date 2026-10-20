"""Text similarity backend.
Uses a pretrained sentence-embedding model when `sentence-transformers` is installed (and the model
can be downloaded); otherwise falls back to character n-gram TF-IDF so the prototype always runs."""
import numpy as np

import config

# Global variables to cache the loaded model instance or record load failures
_st_model = None
_st_failed = False


def _load_st():
    """Lazily load the SentenceTransformer model defined in config.
    
    If the package is not installed or download fails, gracefully falls back
    to TF-IDF by toggling `_st_failed`.
    """
    global _st_model, _st_failed
    if _st_model is not None or _st_failed:
        return _st_model
    try:
        from sentence_transformers import SentenceTransformer
        _st_model = SentenceTransformer(config.EMBEDDING_MODEL)
    except Exception as e:
        print(f"[embedder] sentence-transformers unavailable ({type(e).__name__}); using TF-IDF fallback")
        _st_failed = True
    return _st_model


def backend_name() -> str:
    """Return a human-readable identifier for the active similarity backend."""
    return f"sentence-transformers:{config.EMBEDDING_MODEL}" if _load_st() else "tfidf-char-ngrams (fallback)"


# Cache for pre-computed document embeddings to avoid re-encoding invariant topic lists
_doc_cache: dict = {}


def similarities(query: str, docs: list[str]) -> np.ndarray:
    """Cosine similarity of `query` to each doc, clipped to [0, 1].
    
    Args:
        query: The user input idea/search string.
        docs: List of document strings (e.g. topic texts) to compare against.
        
    Returns:
        1D numpy array of similarity scores corresponding to each doc in `docs`.
    """
    if not docs:
        return np.array([])
    model = _load_st()
    if model is not None:
        # Sentence-transformers path: use normalized embeddings for fast dot-product cosine similarity
        key = tuple(docs)
        if key not in _doc_cache:
            _doc_cache.clear()  # Keep simple single-entry cache for the active candidate set
            _doc_cache[key] = model.encode(docs, normalize_embeddings=True)
        q = model.encode([query], normalize_embeddings=True)[0]
        sims = _doc_cache[key] @ q
    else:
        # Fallback path: sublinear TF-IDF over character n-grams (robust to typos and out-of-vocab words)
        from sklearn.feature_extraction.text import TfidfVectorizer
        vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True, lowercase=True)
        m = vec.fit_transform(docs + [query])
        # Last row corresponds to query; inner product gives cosine similarity since vectors are L2-normalized
        sims = (m[:-1] @ m[-1].T).toarray().ravel()   # rows are L2-normalised -> cosine
    return np.clip(sims, 0.0, 1.0)

