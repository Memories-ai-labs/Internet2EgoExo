/*
 * Video Searching Agent — UI behaviour
 *
 * Talks to POST /api/v1/queries/stream and renders the SSE event stream
 * (started / progress / tool_call / tool_result / clarification_needed /
 * complete / error) as it arrives. No build step, no dependencies.
 */

const API_BASE = "/api/v1";
const STORAGE_KEY_API = "vsa.apiKey";
const STORAGE_KEY_SOURCES = "vsa.sources";

const SOURCE_LABELS = {
  youtube: "YouTube",
  tiktok: "TikTok",
  instagram: "Instagram",
  twitter: "X",
  web: "Web",
};

const el = (id) => document.getElementById(id);

const dom = {
  composer: el("composer"),
  query: el("query"),
  searchBtn: el("search-btn"),
  stopBtn: el("stop-btn"),
  sources: el("sources"),
  sourcesHint: el("sources-hint"),
  examples: el("examples"),
  settings: el("settings"),
  settingsToggle: el("settings-toggle"),
  apiKey: el("api-key"),
  health: el("health"),
  run: el("run"),
  answerPanel: el("answer-panel"),
  answer: el("answer"),
  answerMeta: el("answer-meta"),
  clarifyPanel: el("clarify-panel"),
  clarifyQuestion: el("clarify-question"),
  clarifyOptions: el("clarify-options"),
  clarifyForm: el("clarify-form"),
  clarifyInput: el("clarify-input"),
  errorPanel: el("error-panel"),
  errorMessage: el("error-message"),
  videosPanel: el("videos-panel"),
  videos: el("videos"),
  videosCount: el("videos-count"),
  activity: el("activity"),
  activityStep: el("activity-step"),
  statsPanel: el("stats-panel"),
  stats: el("stats"),
};

const state = {
  selected: new Set(),
  running: false,
  controller: null,
  lastQuery: "",
};

/* ------------------------------------------------------------ formatting */

const escapeHtml = (value) =>
  String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");

const compactNumber = (value) => {
  if (typeof value !== "number" || !Number.isFinite(value)) return null;
  if (value < 1000) return String(value);
  const units = [
    [1e9, "B"],
    [1e6, "M"],
    [1e3, "K"],
  ];
  for (const [size, suffix] of units) {
    if (value >= size) {
      const scaled = value / size;
      return `${scaled >= 10 ? Math.round(scaled) : scaled.toFixed(1)}${suffix}`;
    }
  }
  return String(value);
};

/** Inline markdown: bold, code, links. Input is escaped first. */
const inlineMarkdown = (text) =>
  escapeHtml(text)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[\s(])\*([^*\n]+)\*/g, "$1<em>$2</em>")
    .replace(
      /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
      '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>',
    )
    .replace(
      /(^|[\s(])(https?:\/\/[^\s<)]+)/g,
      '$1<a href="$2" target="_blank" rel="noopener noreferrer">$2</a>',
    );

/** Block markdown: headings, bullets, numbered lists, paragraphs. */
const renderMarkdown = (raw) => {
  const lines = String(raw ?? "").split(/\r?\n/);
  const out = [];
  let list = null; // "ul" | "ol" | null

  const closeList = () => {
    if (list) {
      out.push(`</${list}>`);
      list = null;
    }
  };

  for (const line of lines) {
    const trimmed = line.trim();

    if (!trimmed) {
      closeList();
      continue;
    }

    const heading = trimmed.match(/^#{1,6}\s+(.*)$/);
    if (heading) {
      closeList();
      out.push(`<h3>${inlineMarkdown(heading[1])}</h3>`);
      continue;
    }

    const bullet = trimmed.match(/^[-*•]\s+(.*)$/);
    if (bullet) {
      if (list !== "ul") {
        closeList();
        out.push("<ul>");
        list = "ul";
      }
      out.push(`<li>${inlineMarkdown(bullet[1])}</li>`);
      continue;
    }

    const numbered = trimmed.match(/^\d+[.)]\s+(.*)$/);
    if (numbered) {
      if (list !== "ol") {
        closeList();
        out.push("<ol>");
        list = "ol";
      }
      out.push(`<li>${inlineMarkdown(numbered[1])}</li>`);
      continue;
    }

    closeList();
    out.push(`<p>${inlineMarkdown(trimmed)}</p>`);
  }

  closeList();
  return out.join("");
};

/* ------------------------------------------------------------ sources */

const selectedSources = () => [...state.selected];

const syncSourceChips = () => {
  const chips = dom.sources.querySelectorAll(".chip");
  chips.forEach((chip) => {
    const source = chip.dataset.source;
    const active = source === "auto" ? state.selected.size === 0 : state.selected.has(source);
    chip.classList.toggle("is-active", active);
    chip.setAttribute("aria-pressed", String(active));
  });

  dom.sourcesHint.textContent = state.selected.size
    ? `Pinned to ${selectedSources().map((s) => SOURCE_LABELS[s] ?? s).join(", ")} — the agent will not look elsewhere.`
    : "Auto lets the agent pick sources from your query.";

  localStorage.setItem(STORAGE_KEY_SOURCES, JSON.stringify(selectedSources()));
};

dom.sources.addEventListener("click", (event) => {
  const chip = event.target.closest(".chip");
  if (!chip) return;

  const source = chip.dataset.source;
  if (source === "auto") {
    state.selected.clear();
  } else if (state.selected.has(source)) {
    state.selected.delete(source);
  } else {
    state.selected.add(source);
  }
  syncSourceChips();
});

/* ------------------------------------------------------------ activity */

const addEvent = (kind, html, { live = false } = {}) => {
  document.querySelectorAll(".event.is-live").forEach((node) => node.classList.remove("is-live"));

  const item = document.createElement("li");
  item.className = `event${live ? " is-live" : ""}`;
  item.dataset.kind = kind;
  item.innerHTML = `<span class="event__text">${html}</span>`;
  dom.activity.appendChild(item);
  dom.activity.scrollTop = dom.activity.scrollHeight;
  return item;
};

/* ------------------------------------------------------------ rendering */

const videoCard = (video) => {
  const platform = String(video.platform ?? "other").toLowerCase();
  const url = typeof video.url === "string" ? video.url : "";
  const safeUrl = /^https?:\/\//i.test(url) ? escapeHtml(url) : "";
  const title = video.title || "Untitled video";
  const creator = video.creator ? `@${String(video.creator).replace(/^@/, "")}` : null;

  const metrics = [
    ["views", compactNumber(video.views)],
    ["likes", compactNumber(video.likes)],
    ["comments", compactNumber(video.comments)],
  ]
    .filter(([, value]) => value !== null)
    .map(([label, value]) => `<span><b>${value}</b> ${label}</span>`);

  if (typeof video.engagement_rate === "number" && Number.isFinite(video.engagement_rate)) {
    metrics.push(`<span><b>${(video.engagement_rate * 100).toFixed(1)}%</b> eng</span>`);
  }

  const thumb = video.thumbnail_url && /^https?:\/\//i.test(video.thumbnail_url)
    ? `<img src="${escapeHtml(video.thumbnail_url)}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.remove()" />`
    : "";

  const card = document.createElement("article");
  card.className = "card";
  card.innerHTML = `
    ${safeUrl
      ? `<a class="card__thumb${thumb ? "" : " card__thumb--empty"}" href="${safeUrl}" target="_blank" rel="noopener noreferrer">
           ${thumb || "no preview"}
           <span class="card__badge" data-platform="${escapeHtml(platform)}">${escapeHtml(platform)}</span>
           ${video.duration ? `<span class="card__duration">${escapeHtml(video.duration)}</span>` : ""}
         </a>`
      : `<div class="card__thumb card__thumb--empty">
           ${thumb || "no preview"}
           <span class="card__badge" data-platform="${escapeHtml(platform)}">${escapeHtml(platform)}</span>
         </div>`}
    <div class="card__body">
      <h3 class="card__title">${
        safeUrl
          ? `<a href="${safeUrl}" target="_blank" rel="noopener noreferrer">${escapeHtml(title)}</a>`
          : escapeHtml(title)
      }</h3>
      ${creator ? `<span class="card__creator">${escapeHtml(creator)}</span>` : ""}
      ${video.relevance_note ? `<p class="card__note">${escapeHtml(video.relevance_note)}</p>` : ""}
      ${metrics.length ? `<div class="card__metrics">${metrics.join("")}</div>` : ""}
    </div>`;
  return card;
};

const renderStats = (response) => {
  const cost = response.usage_metrics?.total_cost_usd;
  const entries = [
    ["Videos", response.video_references?.length ?? 0],
    ["Analysed", response.total_videos_analyzed ?? 0],
    ["Steps", response.steps_taken ?? 0],
    ["Tools", response.tools_used?.length ?? 0],
    ["Time", response.execution_time_seconds != null ? `${response.execution_time_seconds}s` : "—"],
    ["Cost", typeof cost === "number" ? `$${cost.toFixed(4)}` : "—"],
  ];

  const sources = response.platforms_searched?.length
    ? response.platforms_searched.map((p) => SOURCE_LABELS[p] ?? p).join(", ")
    : null;

  dom.stats.innerHTML =
    entries
      .map(([label, value]) => `<div><dt>${label}</dt><dd>${escapeHtml(value)}</dd></div>`)
      .join("") +
    (sources
      ? `<div style="grid-column:1/-1"><dt>Sources searched</dt><dd style="font-size:0.8125rem">${escapeHtml(sources)}</dd></div>`
      : "");
  dom.statsPanel.hidden = false;
};

const renderComplete = (response) => {
  dom.answer.innerHTML = renderMarkdown(response.answer);
  dom.answerMeta.textContent = response.parsed_query?.query_type
    ? String(response.parsed_query.query_type).replace(/_/g, " ")
    : "";
  dom.answerPanel.hidden = false;

  const videos = Array.isArray(response.video_references) ? response.video_references : [];
  dom.videos.innerHTML = "";
  videos.forEach((video) => dom.videos.appendChild(videoCard(video)));
  dom.videosCount.textContent = videos.length ? `${videos.length} found` : "";
  dom.videosPanel.hidden = videos.length === 0;

  renderStats(response);
};

const showError = (message) => {
  dom.errorMessage.textContent = message;
  dom.errorPanel.hidden = false;
};

const resetRun = () => {
  dom.run.hidden = false;
  dom.activity.innerHTML = "";
  dom.activityStep.textContent = "";
  dom.answerPanel.hidden = true;
  dom.videosPanel.hidden = true;
  dom.clarifyPanel.hidden = true;
  dom.errorPanel.hidden = true;
  dom.statsPanel.hidden = true;
  dom.videos.innerHTML = "";
  dom.clarifyOptions.innerHTML = "";
  dom.clarifyInput.value = "";
};

const setRunning = (running) => {
  state.running = running;
  dom.searchBtn.disabled = running;
  dom.searchBtn.textContent = running ? "Searching…" : "Search";
  dom.stopBtn.hidden = !running;
};

/* ------------------------------------------------------------ streaming */

const handleEvent = (name, payload) => {
  switch (name) {
    case "started":
      addEvent("start", `Session <b>${escapeHtml(String(payload.session_id).slice(0, 8))}</b> started`, {
        live: true,
      });
      break;

    case "progress":
      dom.activityStep.textContent = payload.max_steps
        ? `step ${payload.step}/${payload.max_steps}`
        : "";
      addEvent("progress", escapeHtml(payload.message ?? ""), { live: true });
      break;

    case "tool_call":
      addEvent("tool_call", `Calling <b>${escapeHtml(payload.tool ?? "tool")}</b>`, { live: true });
      break;

    case "tool_result": {
      const found =
        typeof payload.videos_found === "number" ? ` — ${payload.videos_found} videos` : "";
      if (payload.success) {
        addEvent("tool_ok", `<b>${escapeHtml(payload.tool ?? "tool")}</b> done${escapeHtml(found)}`);
      } else {
        addEvent(
          "tool_fail",
          `<b>${escapeHtml(payload.tool ?? "tool")}</b> failed${
            payload.error ? ` — ${escapeHtml(payload.error)}` : ""
          }`,
        );
      }
      break;
    }

    case "clarification_needed": {
      dom.clarifyQuestion.textContent = payload.question ?? "Could you be more specific?";
      dom.clarifyOptions.innerHTML = "";
      (payload.options ?? []).forEach((option) => {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "chip";
        button.textContent = option;
        button.addEventListener("click", () => runQuery(state.lastQuery, option));
        dom.clarifyOptions.appendChild(button);
      });
      dom.clarifyPanel.hidden = false;
      addEvent("done", "Waiting on a clarification");
      break;
    }

    case "complete":
      renderComplete(payload);
      addEvent("done", "Complete");
      break;

    case "error":
      showError(payload.message || "Unknown error");
      addEvent("tool_fail", `Error: ${escapeHtml(payload.message ?? "unknown")}`);
      break;

    default:
      break;
  }
};

/**
 * Parse an SSE chunk buffer, dispatching every complete message.
 * Handles both LF and CRLF framing (sse-starlette emits CRLF).
 */
const consumeBuffer = (buffer) => {
  const parts = buffer.split(/\r?\n\r?\n/);
  const remainder = parts.pop() ?? "";

  for (const block of parts) {
    let name = "message";
    const dataLines = [];

    for (const line of block.split(/\r?\n/)) {
      if (!line || line.startsWith(":")) continue; // keep-alive comment
      if (line.startsWith("event:")) name = line.slice(6).trim();
      else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
    }

    if (!dataLines.length) continue;

    let payload = {};
    try {
      payload = JSON.parse(dataLines.join("\n"));
    } catch {
      continue;
    }
    handleEvent(name, payload);
  }

  return remainder;
};

const runQuery = async (query, clarification = null) => {
  if (state.running || !query.trim()) return;

  state.lastQuery = query;
  resetRun();
  setRunning(true);

  const controller = new AbortController();
  state.controller = controller;

  const headers = { "Content-Type": "application/json" };
  const apiKey = dom.apiKey.value.trim();
  if (apiKey) headers["X-API-Key"] = apiKey;

  const body = { query };
  if (clarification) body.clarification = clarification;
  const sources = selectedSources();
  if (sources.length) body.sources = sources;

  try {
    const response = await fetch(`${API_BASE}/queries/stream`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
      signal: controller.signal,
    });

    if (!response.ok) {
      let detail = `HTTP ${response.status}`;
      try {
        const problem = await response.json();
        detail = problem.message || problem.detail || detail;
      } catch {
        /* non-JSON error body */
      }
      showError(
        response.status === 401
          ? `${detail} — set your API key from the top-right button.`
          : detail,
      );
      return;
    }

    if (!response.body) {
      showError("This browser cannot read streaming responses.");
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      buffer = consumeBuffer(buffer);
    }
    consumeBuffer(`${buffer}\n\n`);
  } catch (error) {
    if (error.name === "AbortError") addEvent("tool_fail", "Stopped");
    else showError(error.message || String(error));
  } finally {
    setRunning(false);
    state.controller = null;
    document.querySelectorAll(".event.is-live").forEach((n) => n.classList.remove("is-live"));
  }
};

/* ------------------------------------------------------------ wiring */

dom.composer.addEventListener("submit", (event) => {
  event.preventDefault();
  runQuery(dom.query.value);
});

dom.query.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
    event.preventDefault();
    dom.composer.requestSubmit();
  }
});

dom.stopBtn.addEventListener("click", () => state.controller?.abort());

dom.examples.addEventListener("click", (event) => {
  const example = event.target.closest(".example");
  if (!example) return;
  dom.query.value = example.dataset.query ?? example.textContent.trim();
  dom.query.focus();
});

dom.clarifyForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const answer = dom.clarifyInput.value.trim();
  if (answer) runQuery(state.lastQuery, answer);
});

dom.settingsToggle.addEventListener("click", () => {
  const open = dom.settings.hidden;
  dom.settings.hidden = !open;
  dom.settingsToggle.setAttribute("aria-expanded", String(open));
  if (open) dom.apiKey.focus();
});

dom.apiKey.addEventListener("change", () => {
  const value = dom.apiKey.value.trim();
  if (value) localStorage.setItem(STORAGE_KEY_API, value);
  else localStorage.removeItem(STORAGE_KEY_API);
});

const checkHealth = async () => {
  const dot = dom.health.querySelector(".status__dot");
  const label = dom.health.querySelector(".status__label");
  try {
    const response = await fetch(`${API_BASE}/health`);
    const data = await response.json();
    const { healthy = 0, total = 0 } = data.tools ?? {};
    dot.dataset.state = healthy === 0 ? "down" : healthy < total ? "degraded" : "ok";
    label.textContent = `${healthy}/${total} tools`;
    dom.health.title = Object.entries(data.tools?.details ?? {})
      .map(([tool, info]) => `${tool}: ${info.healthy ? "ok" : info.error || "unavailable"}`)
      .join("\n");
  } catch {
    dot.dataset.state = "down";
    label.textContent = "offline";
  }
};

const restore = () => {
  const savedKey = localStorage.getItem(STORAGE_KEY_API);
  if (savedKey) dom.apiKey.value = savedKey;

  try {
    const savedSources = JSON.parse(localStorage.getItem(STORAGE_KEY_SOURCES) ?? "[]");
    if (Array.isArray(savedSources)) {
      savedSources
        .filter((source) => source in SOURCE_LABELS)
        .forEach((source) => state.selected.add(source));
    }
  } catch {
    /* ignore malformed storage */
  }
  syncSourceChips();
};

restore();
checkHealth();
