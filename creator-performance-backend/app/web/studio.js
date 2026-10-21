"use strict";

(() => {
  const $ = (id) => document.getElementById(id);
  const state = { file: null, objectURL: null, busy: false, report: null, runs: [] };
  const metricDefinitions = [
    { key: "brightness", label: "Brightness", unit: "Mean luminance · 0–1" },
    { key: "contrast", label: "Contrast", unit: "Luminance standard deviation" },
    { key: "saturation", label: "Saturation", unit: "Mean HSV saturation" },
    { key: "text_coverage", label: "Text-region coverage", unit: "Detected region area, not word count" },
  ];
  const categoryLabels = { cooking: "Cooking", education: "Education", gaming: "Gaming" };
  const languageLabels = { en: "English", si: "Sinhala", ta: "Tamil", mixed: "Mixed", unknown: "Language unspecified" };

  function node(tag, className, text) {
    const result = document.createElement(tag);
    if (className) result.className = className;
    if (text !== undefined) result.textContent = text;
    return result;
  }

  function finite(value) { return typeof value === "number" && Number.isFinite(value); }
  function format(value, key) {
    if (!finite(value)) return "Unavailable";
    if (key === "saturation" || key === "text_coverage") return `${(value * 100).toFixed(1)}%`;
    if (["brightness", "contrast", "image_title_alignment"].includes(key)) return value.toFixed(3);
    return Number.isInteger(value) ? String(value) : value.toFixed(2);
  }
  function friendly(value) { return String(value).replaceAll("_", " "); }
  function safePreview(value) {
    return typeof value === "string" && /^data:image\/(jpeg|png|webp);base64,[A-Za-z0-9+/=]+$/.test(value) ? value : "";
  }
  function previewImage(src, alt) {
    const image = node("img");
    image.src = safePreview(src);
    image.alt = alt;
    image.loading = "lazy";
    return image;
  }

  function showError(message) {
    $("form-error").textContent = message;
    $("form-error").hidden = !message;
  }

  function setBusy(busy, message = "") {
    state.busy = busy;
    document.body.classList.toggle("busy", busy);
    $("results-column").setAttribute("aria-busy", String(busy));
    document.querySelectorAll("#analyze-form input, #analyze-form textarea, #analyze-form select, #analyze-form button, .sample-card").forEach((control) => { control.disabled = busy; });
    $("analyze-label").textContent = busy ? "Working on it…" : "Analyze thumbnail";
    $("request-status").textContent = message;
  }

  async function request(url, options = {}, timeout = 30000) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeout);
    try {
      const response = await fetch(url, { ...options, signal: controller.signal });
      const data = await response.json().catch(() => null);
      if (!response.ok) {
        let message = data?.detail;
        if (Array.isArray(message)) message = message.map((item) => `${item.loc?.slice(1).join(" / ") || "Input"}: ${item.msg}`).join(". ");
        throw new Error(typeof message === "string" ? message : `The request failed (${response.status}). Check the backend terminal for details.`);
      }
      if (!data) throw new Error("The service returned an unreadable response.");
      return data;
    } catch (error) {
      if (error.name === "AbortError") throw new Error("The request timed out. The first analysis loads local models and can take longer. Check the backend terminal before retrying.");
      if (error instanceof TypeError) throw new Error("Could not reach the local service. Make sure the backend is running, then try again.");
      throw error;
    } finally { clearTimeout(timer); }
  }

  function selectFile(file) {
    if (state.busy || !file) return;
    showError("");
    if (!["image/jpeg", "image/png", "image/webp"].includes(file.type) || file.size > 10 * 1024 * 1024) {
      showError("Choose a JPG, PNG or WebP image up to 10 MiB.");
      // Reset both the visible selection and submitted file after an invalid replacement.
      state.file = null;
      $("thumbnail").value = "";
      if (state.objectURL) URL.revokeObjectURL(state.objectURL);
      state.objectURL = null;
      $("upload-preview").removeAttribute("src");
      $("upload-preview").hidden = true;
      $("drop-placeholder").hidden = false;
      $("replace-label").hidden = true;
      $("file-info").textContent = "Your upload is processed locally by this backend.";
      return;
    }
    state.file = file;
    if (state.objectURL) URL.revokeObjectURL(state.objectURL);
    state.objectURL = URL.createObjectURL(file);
    $("upload-preview").src = state.objectURL;
    $("upload-preview").hidden = false;
    $("drop-placeholder").hidden = true;
    $("replace-label").hidden = false;
    $("file-info").textContent = `${file.name} · ${(file.size / 1024).toFixed(0)} KiB · ready to analyze`;
  }

  $("thumbnail").addEventListener("change", (event) => selectFile(event.target.files[0]));
  for (const eventName of ["dragenter", "dragover"]) {
    $("dropzone").addEventListener(eventName, (event) => {
      event.preventDefault();
      if (!state.busy) $("dropzone").classList.add("drag-over");
    });
  }
  for (const eventName of ["dragleave", "drop"]) {
    $("dropzone").addEventListener(eventName, (event) => {
      event.preventDefault();
      $("dropzone").classList.remove("drag-over");
    });
  }
  $("dropzone").addEventListener("drop", (event) => {
    if (state.busy) return;
    const file = event.dataTransfer.files[0];
    if (!file) return;
    const transfer = new DataTransfer();
    transfer.items.add(file);
    $("thumbnail").files = transfer.files;
    selectFile(file);
  });
  // Avoid accidental browser navigation when a file is dropped just outside the target.
  window.addEventListener("dragover", (event) => { if (event.dataTransfer.types.includes("Files")) event.preventDefault(); });
  window.addEventListener("drop", (event) => { if (event.dataTransfer.types.includes("Files")) event.preventDefault(); });

  $("analyze-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (state.busy) return;
    if (!state.file) { showError("Choose a thumbnail first."); return; }
    const title = $("title").value.trim();
    if (!title) { showError("Enter a video title."); $("title").focus(); return; }
    const context = { title, category: $("category").value, language: $("title-language").value, source: "live" };
    const body = new FormData();
    body.append("thumbnail", state.file);
    body.append("title", title);
    body.append("category", context.category);
    body.append("title_language", context.language);
    showError("");
    setBusy(true, "Analyzing your image. The first request also loads cached models; please keep this tab open.");
    const started = performance.now();
    try {
      const report = await request("/api/module-c/analyze", { method: "POST", body }, 300000);
      state.runs.push({ report, context });
      state.runs = state.runs.slice(-2);
      renderReport(report, context);
      $("request-status").textContent = `Analysis complete in ${((performance.now() - started) / 1000).toFixed(1)} seconds. Select another image to explore a revision.`;
    } catch (error) { showError(error.message); $("request-status").textContent = ""; }
    finally { setBusy(false, $("request-status").textContent); }
  });

  function renderCapabilities(report) {
    const row = $("capability-row");
    row.replaceChildren();
    for (const [label, status] of [
      ["Image embeddings", report.capabilities.image_embeddings],
      ["Text detection", report.capabilities.text_detection],
      ["Historical library", report.capabilities.historical_comparison],
    ]) {
      const available = status === "available";
      row.append(node("span", `capability-pill${available ? "" : " unavailable"}`, `${label} · ${available ? "available" : friendly(status)}`));
    }
    row.append(node("span", "capability-pill", `Wording · ${report.wording.provider}${report.wording.status === "fallback" ? " fallback" : ""}`));
  }

  function renderMetrics(report) {
    const container = $("metrics");
    container.replaceChildren();
    for (const definition of metricDefinitions) {
      const finding = report.findings.find((item) => item.metric === definition.key);
      const card = node("div", "metric");
      const heading = node("div", "metric-heading");
      heading.append(node("span", "", definition.label), node("strong", "", format(report.measurements[definition.key], definition.key)));
      card.append(heading);
      if (finite(finding?.percentile)) {
        const bar = node("div", "metric-bar");
        bar.setAttribute("aria-hidden", "true");
        const fill = node("div", "metric-fill");
        fill.style.width = `${Math.max(0, Math.min(100, finding.percentile))}%`;
        bar.append(fill);
        card.append(bar, node("p", "", `Percentile ${finding.percentile} · ${finding.reference_count.toLocaleString()} ${categoryLabels[report.category].toLowerCase()} references`));
      } else card.append(node("p", "", "Category percentile unavailable"));
      card.append(node("p", "", definition.unit));
      container.append(card);
    }
  }

  function renderSuggestions(report) {
    $("suggestion-count").textContent = `${report.recommendations.length} IDEAS`;
    $("suggestions").replaceChildren();
    for (const recommendation of report.recommendations) {
      const card = node("article", "suggestion");
      const content = node("div");
      content.append(node("h4", "", recommendation.action), node("p", "", recommendation.explanation));
      const test = node("p", "test-step");
      test.append(node("strong", "", "Try this: "), document.createTextNode(recommendation.how_to_test));
      const evidence = node("details");
      evidence.append(node("summary", "", "Why this suggestion?"));
      for (const id of recommendation.evidence_ids) {
        const finding = report.findings.find((item) => item.id === id);
        evidence.append(node("p", "", finding ? finding.statement : `Evidence: ${id}`));
      }
      content.append(test, evidence);
      card.append(node("span", "suggestion-number", String(recommendation.priority).padStart(2, "0")), content);
      $("suggestions").append(card);
    }
  }

  function renderNeighbors(report) {
    const container = $("neighbors");
    container.replaceChildren();
    if (!report.historical_comparisons.length) {
      container.append(node("p", "small-copy", "No historical comparisons are available for this report. Check the image-embedding and reference-library statuses above."));
    }
    for (const comparison of report.historical_comparisons) {
      const card = node("article", "neighbor-card");
      if (safePreview(comparison.thumbnail_preview)) card.append(previewImage(comparison.thumbnail_preview, `Historical thumbnail ${comparison.video_id}`));
      else card.append(node("div", "neighbor-missing", "Preview unavailable"));
      const content = node("div", "neighbor-content");
      const link = node("a", "", `View source ↗ · ${comparison.video_id}`);
      // Historical links are constructed from IDs; never navigate to arbitrary returned URLs.
      if (/^[A-Za-z0-9_-]{1,32}$/.test(comparison.video_id)) link.href = `https://www.youtube.com/watch?v=${encodeURIComponent(comparison.video_id)}`;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      content.append(link, node("p", "", `Visual cosine: ${comparison.visual_similarity.toFixed(3)}`));
      content.append(node("span", "neighbor-outcome", comparison.outcome === "above_neighbor_baseline" ? "Historically above its channel’s neighboring-upload baseline" : "Historically at or below its channel’s neighboring-upload baseline"));
      content.append(node("p", "", `Relative log views: ${comparison.relative_view_performance.toFixed(3)} · not CTR`));
      card.append(content);
      container.append(card);
    }
  }

  function addPair(container, label, value) {
    container.append(node("dt", "", label), node("dd", "", value === null || value === undefined ? "Unavailable" : String(value)));
  }

  function renderEvidence(report) {
    $("findings").replaceChildren();
    for (const finding of report.findings) {
      const item = node("div", "finding");
      item.append(node("b", "", `${friendly(finding.basis).toUpperCase()} · ${finding.id}`), document.createTextNode(finding.statement));
      $("findings").append(item);
    }
    $("extra-measurements").replaceChildren();
    for (const [key, value] of Object.entries(report.measurements)) {
      if (!metricDefinitions.some((definition) => definition.key === key)) addPair($("extra-measurements"), friendly(key), format(value, key));
    }
    for (const [key, value] of Object.entries(report.title_features)) addPair($("extra-measurements"), friendly(key), value);
    addPair($("extra-measurements"), "English image–title cosine", format(report.image_title_alignment, "image_title_alignment"));
    $("provenance").replaceChildren();
    for (const [key, value] of Object.entries(report.capabilities)) addPair($("provenance"), friendly(key), friendly(value));
    for (const [key, value] of Object.entries(report.provenance)) addPair($("provenance"), friendly(key), value);
    if (report.wording.reason) addPair($("provenance"), "Wording fallback reason", report.wording.reason);
    $("limitations").replaceChildren(...report.limitations.map((limitation) => node("li", "", limitation)));
  }

  function renderRevisions(context) {
    const comparable = context.source === "live" && state.runs.length === 2 && state.runs[0].context.category === state.runs[1].context.category;
    $("revision-section").hidden = !comparable;
    if (!comparable) return;
    $("revision-previews").replaceChildren();
    for (const [index, run] of state.runs.entries()) {
      const figure = node("figure");
      figure.append(previewImage(run.report.mobile_preview, index ? "Current thumbnail" : "Previous thumbnail"), node("figcaption", "", `${index ? "Current" : "Previous"}: ${run.context.title}`));
      $("revision-previews").append(figure);
    }
    $("revision-metrics").replaceChildren();
    for (const { key, label } of metricDefinitions) {
      const previous = state.runs[0].report.measurements[key];
      const current = state.runs[1].report.measurements[key];
      let delta = "Unavailable";
      if (finite(previous) && finite(current)) {
        const difference = current - previous;
        delta = ["saturation", "text_coverage"].includes(key) ? `${difference > 0 ? "+" : ""}${(difference * 100).toFixed(1)} pp` : `${difference > 0 ? "+" : ""}${difference.toFixed(3)}`;
      }
      const row = node("tr");
      row.append(node("th", "", label), node("td", "", format(previous, key)), node("td", "", format(current, key)), node("td", "", delta));
      $("revision-metrics").append(row);
    }
  }

  function renderReport(report, context) {
    state.report = report;
    $("empty-state").hidden = true;
    $("report").hidden = false;
    $("report-source").textContent = context.source === "live" ? "LIVE UPLOAD / LOCAL ANALYSIS" : "SAVED PUBLIC-CORPUS EXAMPLE / PRECOMPUTED REPORT";
    $("report-context").textContent = `${categoryLabels[report.category]} · ${languageLabels[report.title_language]} · ${context.title}`;
    $("mobile-preview").src = safePreview(report.mobile_preview);
    $("preview-title").textContent = context.title;
    renderCapabilities(report);
    renderMetrics(report);
    renderSuggestions(report);
    renderNeighbors(report);
    renderEvidence(report);
    renderRevisions(context);
    $("report-heading").focus({ preventScroll: true });
    $("report").scrollIntoView({ behavior: "smooth", block: "start" });
  }

  $("download-report").addEventListener("click", () => {
    if (!state.report) return;
    const url = URL.createObjectURL(new Blob([JSON.stringify(state.report, null, 2)], { type: "application/json" }));
    const link = node("a");
    link.href = url;
    link.download = `frame-report-${Date.now()}.json`;
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
  $("print-report").addEventListener("click", () => window.print());

  async function loadExamples() {
    try {
      const catalog = await request("/api/module-c/examples");
      $("sample-status").textContent = catalog.examples.length ? "" : "Saved examples are not available yet. Generate the review queue to enable them; live uploads work independently.";
      for (const example of catalog.examples) {
        const card = node("button", "sample-card");
        card.type = "button";
        card.disabled = state.busy;
        card.setAttribute("aria-label", `View saved ${example.category} example: ${example.title}`);
        const copy = node("span", "sample-copy");
        copy.append(node("span", "sample-category", categoryLabels[example.category]), node("span", "sample-title", example.title), node("span", "sample-link", "View saved analysis ↗"));
        card.append(previewImage(example.thumbnail_preview, `${example.category} sample thumbnail`), copy);
        card.addEventListener("click", async () => {
          if (state.busy) return;
          showError("");
          setBusy(true, "Loading a saved public-corpus report…");
          try {
            const report = await request(`/api/module-c/examples/${encodeURIComponent(example.video_id)}`);
            renderReport(report, { title: example.title, source: "saved" });
            $("request-status").textContent = "Saved example loaded. Upload your own thumbnail for a new analysis.";
          } catch (error) { showError(error.message); $("request-status").textContent = ""; }
          finally { setBusy(false, $("request-status").textContent); }
        });
        $("samples").append(card);
      }
    } catch (error) { $("sample-status").textContent = `Could not load saved examples. ${error.message}`; }
  }

  async function loadStatus() {
    try {
      const status = await request("/api/module-c/status");
      $("reference-count").textContent = status.reference_rows.toLocaleString();
      $("service-status").textContent = status.reference_index === "available" ? "● Library ready · unseen test channels excluded" : `Library ${friendly(status.reference_index)} · measurements still available`;
    } catch (error) {
      $("reference-count").textContent = "Offline";
      $("service-status").textContent = error.message;
    }
  }

  window.addEventListener("beforeunload", () => { if (state.objectURL) URL.revokeObjectURL(state.objectURL); });
  loadStatus();
  loadExamples();
})();
