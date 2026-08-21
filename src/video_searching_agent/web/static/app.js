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
const STORAGE_KEY_REQS = "vsa.requirements";

const SOURCE_LABELS = {
  youtube: "YouTube",
  tiktok: "TikTok",
  instagram: "Instagram",
  twitter: "X",
  web: "Web",
};

// Tool names the agent reports, in words a reader recognises.
const TOOL_LABELS = {
  video_search: "web video search",
  youtube_search: "YouTube search",
  youtube_channel_info: "YouTube channel",
  tiktok_search: "TikTok search",
  tiktok_creator_info: "TikTok creator",
  instagram_search: "Instagram search",
  instagram_creator_info: "Instagram creator",
  twitter_search: "X search",
  twitter_profile_info: "X profile",
  exa_search: "neural web search",
  exa_find_similar: "similar pages",
  exa_get_content: "page content",
  exa_research: "deep research",
  video_index: "indexing video",
  video_analysis: "reading video content",
  video_moment_search: "searching indexed moments",
};

const toolLabel = (tool) => TOOL_LABELS[tool] ?? tool;

const el = (id) => document.getElementById(id);

const dom = {
  composer: el("composer"),
  query: el("query"),
  searchBtn: el("search-btn"),
  stopBtn: el("stop-btn"),
  sources: el("sources"),
  viewpoint: el("viewpoint"),
  minDuration: el("min-duration"),
  license: el("license"),
  targetHours: el("target-hours"),
  datasetPanel: el("dataset-panel"),
  dataset: el("dataset"),
  datasetMeta: el("dataset-meta"),
  exportJsonl: el("export-jsonl"),
  exportCsv: el("export-csv"),
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
  datalakePanel: el("datalake-panel"),
  datalake: el("datalake"),
  datalakeMeta: el("datalake-meta"),
  momentsPanel: el("moments-panel"),
  moments: el("moments"),
  momentsCount: el("moments-count"),
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
  viewpoint: "",
  moments: [],
  minDurationSeconds: "",
  licenseFilter: "",
  manifest: null,
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

// Licence values that mean "safe to reuse" — mirrors the backend list.
const REUSABLE_LICENSES = new Set([
  "creativecommon",
  "creative_commons",
  "cc-by",
  "cc0",
  "public",
  "reusable",
]);

/** Human clip length: prefers seconds, falls back to a platform string. */
const durationLabel = (video) => {
  const seconds = video.duration_seconds;
  if (typeof seconds === "number" && Number.isFinite(seconds) && seconds > 0) {
    const whole = Math.floor(seconds);
    const hours = Math.floor(whole / 3600);
    const minutes = Math.floor((whole % 3600) / 60);
    const rest = whole % 60;
    return hours
      ? `${hours}:${String(minutes).padStart(2, "0")}:${String(rest).padStart(2, "0")}`
      : `${minutes}:${String(rest).padStart(2, "0")}`;
  }
  return video.duration ?? "";
};

/** Seconds → m:ss, for moment ranges and transcript turns. */
const timecode = (seconds) => {
  if (typeof seconds !== "number" || !Number.isFinite(seconds)) return null;
  const whole = Math.max(0, Math.floor(seconds));
  const minutes = Math.floor(whole / 60);
  return `${minutes}:${String(whole % 60).padStart(2, "0")}`;
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

/**
 * Wire a single-select chip group: exactly one chip active, its dataset value
 * pushed into `state[stateKey]`.
 */
const wireChoiceGroup = (container, datasetKey, stateKey) => {
  container.addEventListener("click", (event) => {
    const chip = event.target.closest(".chip");
    if (!chip) return;
    state[stateKey] = chip.dataset[datasetKey] ?? "";
    container.querySelectorAll(".chip").forEach((node) => {
      const active = node === chip;
      node.classList.toggle("is-active", active);
      node.setAttribute("aria-pressed", String(active));
    });
    persistRequirements();
  });
};

const persistRequirements = () => {
  try {
    localStorage.setItem(
      STORAGE_KEY_REQS,
      JSON.stringify({
        viewpoint: state.viewpoint,
        minDurationSeconds: state.minDurationSeconds,
        licenseFilter: state.licenseFilter,
        targetHours: dom.targetHours.value,
      }),
    );
  } catch {
    /* storage unavailable */
  }
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

  // Training-data facts, not engagement: viewpoint, length, licence.
  const viewpoint = String(video.viewpoint ?? "unknown").toLowerCase();
  const confidence =
    typeof video.viewpoint_confidence === "number" && video.viewpoint_confidence > 0
      ? `<span class="viewpoint-badge__conf">${video.viewpoint_confidence.toFixed(2)}</span>`
      : "";
  const reusable = REUSABLE_LICENSES.has(String(video.license ?? "").toLowerCase());
  const curation = [
    `<span class="viewpoint-badge" data-viewpoint="${escapeHtml(viewpoint)}" title="${
      escapeHtml((video.viewpoint_evidence ?? []).join(", ")) || "no viewpoint cues found"
    }">${escapeHtml(viewpoint)}${confidence}</span>`,
    video.license
      ? `<span class="license-tag${reusable ? " license-tag--reusable" : ""}">${escapeHtml(
          reusable ? "reusable" : video.license,
        )}</span>`
      : "",
  ]
    .filter(Boolean)
    .join("");

  const metrics = [
    ["length", durationLabel(video)],
    ["score", typeof video.usability_score === "number" && video.usability_score > 0
      ? video.usability_score.toFixed(2)
      : null],
  ]
    .filter(([, value]) => value !== null && value !== "")
    .map(([label, value]) => `<span><b>${escapeHtml(value)}</b> ${label}</span>`);

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
      ${curation ? `<div class="card__curation">${curation}</div>` : ""}
      ${creator ? `<span class="card__creator">${escapeHtml(creator)}</span>` : ""}
      ${video.relevance_note ? `<p class="card__note">${escapeHtml(video.relevance_note)}</p>` : ""}
      ${metrics.length ? `<div class="card__metrics">${metrics.join("")}</div>` : ""}
      <button type="button" class="card__toggle">Annotation tree</button>
    </div>
    <div class="card__tree" hidden></div>`;

  // The tree is built on first open, from the manifest clip plus any moments
  // the run retrieved for this video.
  const toggle = card.querySelector(".card__toggle");
  const treeHost = card.querySelector(".card__tree");
  toggle.addEventListener("click", () => {
    const opening = treeHost.hidden;
    if (opening && !treeHost.dataset.built) {
      const clip =
        (state.manifest?.clips ?? []).find((candidate) => candidate.url === video.url) ?? video;
      treeHost.innerHTML = clipTree(clip, state.moments);
      treeHost.dataset.built = "1";
    }
    treeHost.hidden = !opening;
    card.classList.toggle("card--open", opening);
  });

  return card;
};

/** Render one derived-content block (summary, captions, or transcription). */
const datalakeBlock = (label, value) => {
  if (!value) return "";

  if (Array.isArray(value)) {
    const segments = value
      .filter((segment) => segment && typeof segment === "object")
      .map((segment) => {
        const start = timecode(segment.start);
        const speaker = segment.speaker_id
          ? `<span class="dl-segment__speaker">${escapeHtml(segment.speaker_id)}</span> `
          : "";
        return `<div class="dl-segment">
            <span class="dl-segment__time">${start ? escapeHtml(start) : ""}</span>
            <span>${speaker}${escapeHtml(segment.text ?? "")}</span>
          </div>`;
      })
      .join("");
    if (!segments) return "";
    return `<div class="dl-block">
        <span class="dl-block__label">${escapeHtml(label)}</span>
        <div class="dl-segments">${segments}</div>
      </div>`;
  }

  return `<div class="dl-block">
      <span class="dl-block__label">${escapeHtml(label)}</span>
      <p class="dl-block__text">${escapeHtml(String(value))}</p>
    </div>`;
};

/**
 * Render what the Datalake returned for a video: either the indexing-still-running
 * notice, or its title/summary/captions/transcription.
 */
const renderDatalake = (analyses) => {
  const parts = analyses
    .map((analysis) => {
      const videoId = analysis.video_id ? escapeHtml(String(analysis.video_id)) : "";

      if (analysis.status === "processing") {
        const percent = analysis.progress?.percent;
        return `<div class="dl-status">
            <span class="dl-status__badge">indexing</span>
            <span>Still indexing${
              typeof percent === "number" ? ` — ${escapeHtml(percent)}%` : ""
            }. Ask again to read the results${videoId ? ` (<code>${videoId}</code>)` : ""}.</span>
          </div>`;
      }

      const window = analysis.window
        ? `${timecode(analysis.window.start) ?? "0:00"}–${timecode(analysis.window.end) ?? "end"}`
        : null;
      const duration = timecode(analysis.duration_seconds);

      const header = `<div class="dl-status dl-status--ready">
          <span class="dl-status__badge">ready</span>
          <span>${escapeHtml(analysis.title || "Indexed video")}</span>
          ${duration ? `<span>· ${escapeHtml(duration)}</span>` : ""}
          ${window ? `<span>· window ${escapeHtml(window)}</span>` : ""}
          ${videoId ? `<span>· <code>${videoId}</code></span>` : ""}
        </div>`;

      return (
        header +
        datalakeBlock("Summary", analysis.summary) +
        datalakeBlock("Visual captions", analysis.caption) +
        datalakeBlock("Speech", analysis.transcription)
      );
    })
    .join("");

  dom.datalake.innerHTML = parts;
  dom.datalakeMeta.textContent = analyses.length > 1 ? `${analyses.length} videos` : "";
  dom.datalakePanel.hidden = !parts;
};

/** Render moments returned by video_moment_search. */
const renderMoments = (moments) => {
  state.moments = moments;
  dom.moments.innerHTML = moments
    .map((moment) => {
      const start = timecode(moment.start);
      const end = timecode(moment.end);
      const range = start && end ? `${start}–${end}` : start || "";
      const thumb = /^https?:\/\//i.test(moment.thumbnail_url ?? "")
        ? `<img class="moment__thumb" src="${escapeHtml(moment.thumbnail_url)}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.remove()" />`
        : "";
      const score =
        typeof moment.score === "number" ? `${(moment.score * 100).toFixed(0)}%` : "";

      return `<article class="moment">
          <div class="moment__head">
            ${range ? `<span class="moment__range">${escapeHtml(range)}</span>` : ""}
            ${moment.target ? `<span class="moment__target">${escapeHtml(moment.target)}</span>` : ""}
            ${score ? `<span class="moment__score">${escapeHtml(score)}</span>` : ""}
          </div>
          ${thumb}
          ${moment.snippet ? `<p class="moment__snippet">${escapeHtml(moment.snippet)}</p>` : ""}
          ${moment.ref ? `<span class="moment__ref">${escapeHtml(moment.ref)}</span>` : ""}
        </article>`;
    })
    .join("");

  dom.momentsCount.textContent = moments.length ? `${moments.length} found` : "";
  dom.momentsPanel.hidden = moments.length === 0;
};

/**
 * Pull Datalake payloads out of the run's tool results. The complete event
 * carries each tool's own result, so no extra request is needed.
 */
const extractDatalake = (response) => {
  const analyses = [];
  const moments = [];

  for (const detail of response.tool_execution_details ?? []) {
    if (!detail || detail.success === false) continue;
    const data = detail.result;
    if (!data || typeof data !== "object") continue;

    if (detail.tool === "video_analysis" || detail.tool === "video_index") {
      if (data.status) analyses.push(data);
    } else if (detail.tool === "video_moment_search" && Array.isArray(data.moments)) {
      moments.push(...data.moments.filter((m) => m && typeof m === "object"));
    }
  }

  return { analyses, moments };
};

/** Render the collection manifest: totals, viewpoint mix, exclusions, cost. */
const renderDataset = (manifest) => {
  state.manifest = manifest ?? null;
  if (!manifest || !manifest.total_clips) {
    dom.datasetPanel.hidden = true;
    return;
  }

  const stat = (label, value, extraClass = "") =>
    `<div class="ds-stat"><span class="ds-stat__label">${escapeHtml(label)}</span>
      <span class="ds-stat__value ${extraClass}">${escapeHtml(value)}</span></div>`;

  const viewpointMix = Object.entries(manifest.by_viewpoint ?? {})
    .map(([key, count]) => `${count} ${key}`)
    .join(" · ");
  const platformMix = Object.entries(manifest.by_platform ?? {})
    .map(([key, count]) => `${count} ${key}`)
    .join(" · ");

  const blocks = [
    stat("Clips", String(manifest.total_clips)),
    stat("Hours", manifest.total_hours.toFixed(2)),
    stat("Reusable licence", `${manifest.reusable_license_clips}/${manifest.total_clips}`),
    stat("Known length", `${manifest.clips_with_known_duration}/${manifest.total_clips}`),
  ];

  if (manifest.target_hours) {
    const pct = Math.min((manifest.total_hours / manifest.target_hours) * 100, 100);
    const met = manifest.total_hours >= manifest.target_hours;
    blocks.push(`<div class="ds-target${met ? " ds-target--met" : ""}">
        <span class="ds-stat__label">${
          met ? "Target reached" : "Progress to target"
        } — ${escapeHtml(manifest.total_hours.toFixed(2))}h of ${escapeHtml(
          String(manifest.target_hours),
        )}h</span>
        <div class="ds-target__bar"><div class="ds-target__fill" style="width:${pct.toFixed(
          1,
        )}%"></div></div>
      </div>`);
  }

  if (viewpointMix) {
    blocks.push(stat("Viewpoint mix", viewpointMix, "ds-stat__value--small"));
  }
  if (platformMix) {
    blocks.push(stat("Sources", platformMix, "ds-stat__value--small"));
  }

  if (manifest.excluded_clips) {
    const reasons = Object.entries(manifest.exclusion_reasons ?? {})
      .map(([reason, count]) => `<span><code>${escapeHtml(String(count))}</code> ${escapeHtml(reason)}</span>`)
      .join("");
    blocks.push(`<div class="ds-excluded">
        <span class="ds-stat__label">Excluded ${escapeHtml(String(manifest.excluded_clips))}</span>
        ${reasons}
      </div>`);
  }

  if (manifest.cost) {
    blocks.push(renderCostBlock(manifest.cost));
  }

  dom.dataset.innerHTML = blocks.join("");
  dom.datasetMeta.textContent = manifest.requested_viewpoint
    ? `${manifest.requested_viewpoint} requested`
    : "any viewpoint";
  dom.datasetPanel.hidden = false;
};

/** Cost accounting for the collected set, as reported by the backend. */
const renderCostBlock = (cost) => {
  const money = (value) =>
    typeof value === "number" && Number.isFinite(value) ? `$${value.toFixed(2)}` : "—";
  const rows = [
    ["Discovery", cost.discovery_usd],
    ["Download", cost.download_usd],
    ["Indexing", cost.indexing_usd],
    ["Annotation", cost.annotation_usd],
  ]
    .filter(([, value]) => typeof value === "number")
    .map(([label, value]) => `<span>${escapeHtml(label)} ${escapeHtml(money(value))}</span>`)
    .join(" · ");

  return `<div class="ds-excluded ds-stat--wide">
      <span class="ds-stat__label">Cost per hour</span>
      <span class="ds-stat__value">${escapeHtml(money(cost.usd_per_collected_hour))}<span
        class="viewpoint-badge__conf"> /h collected</span></span>
      <span>${escapeHtml(money(cost.usd_per_delivered_hour))} per delivered hour at
        ${escapeHtml(String(Math.round((cost.assumed_yield ?? 0) * 100)))}% frame-check yield</span>
      <span>${rows}</span>
      <span>Total ${escapeHtml(money(cost.total_usd))} for
        ${escapeHtml((cost.hours ?? 0).toFixed(2))}h</span>
    </div>`;
};

/**
 * The annotation tree for one clip: what was decided about it, span by span.
 * Renders whatever exists — viewpoint evidence always, moments and hand/object
 * annotations once the curation loop has written them — and says plainly when a
 * branch is still empty.
 */
const clipTree = (clip, moments) => {
  const leaf = (label, value) =>
    value ? `<div class="tree__leaf"><span><b>${escapeHtml(label)}</b> ${value}</span></div>` : "";

  const viewpoint = String(clip.viewpoint ?? "unknown").toLowerCase();
  const evidence = (clip.viewpoint_evidence ?? []).length
    ? (clip.viewpoint_evidence ?? [])
        .map((cue) => `<span class="tree__tag">${escapeHtml(cue)}</span>`)
        .join("")
    : "";

  const viewpointNode = `<span class="tree__branch">viewpoint</span>
    <div class="tree__node">
      ${leaf("verdict", `${escapeHtml(viewpoint)} (${
        typeof clip.viewpoint_confidence === "number"
          ? clip.viewpoint_confidence.toFixed(2)
          : "0.00"
      })`)}
      ${
        evidence
          ? `<div class="tree__leaf"><span><b>evidence</b></span></div>
             <div class="tree__tags">${evidence}</div>`
          : '<div class="tree__empty">no viewpoint cues in the available text</div>'
      }
    </div>`;

  const sourceNode = `<span class="tree__branch">source</span>
    <div class="tree__node">
      ${leaf("platform", escapeHtml(String(clip.platform ?? "")))}
      ${leaf("creator", clip.creator ? escapeHtml(String(clip.creator)) : "")}
      ${leaf("length", escapeHtml(durationLabel(clip) || "unknown"))}
      ${leaf("licence", escapeHtml(String(clip.license ?? "unknown")))}
      ${leaf(
        "usability",
        typeof clip.usability_score === "number" ? clip.usability_score.toFixed(2) : "",
      )}
      ${leaf("datalake id", clip.datalake_video_id ? escapeHtml(clip.datalake_video_id) : "")}
    </div>`;

  const annotations = Array.isArray(clip.annotations) ? clip.annotations : [];
  const relatedMoments = (moments ?? []).filter(
    (moment) =>
      clip.datalake_video_id && moment.video_id && moment.video_id === clip.datalake_video_id,
  );

  const annotationRows = annotations
    .map((annotation) => {
      const span =
        annotation.span_start !== null && annotation.span_start !== undefined
          ? `${timecode(annotation.span_start) ?? "0:00"}–${
              timecode(annotation.span_end) ?? "end"
            }`
          : annotation.ref ?? "span";
      const tags = (annotation.tags ?? [])
        .map((tag) => `<span class="tree__tag">${escapeHtml(tag)}</span>`)
        .join("");
      return `<div class="tree__leaf">
          <span><span class="tree__span">${escapeHtml(span)}</span>
          ${annotation.label ? `<b>${escapeHtml(annotation.label)}</b>` : ""}</span>
        </div>
        <div class="tree__node">
          ${
            annotation.left_hand
              ? `<div class="tree__leaf"><span><span class="tree__hand">left hand</span> ${escapeHtml(
                  annotation.left_hand,
                )}</span></div>`
              : ""
          }
          ${
            annotation.right_hand
              ? `<div class="tree__leaf"><span><span class="tree__hand">right hand</span> ${escapeHtml(
                  annotation.right_hand,
                )}</span></div>`
              : ""
          }
          ${
            (annotation.objects ?? []).length
              ? `<div class="tree__leaf"><span><b>objects</b> ${escapeHtml(
                  (annotation.objects ?? []).join(", "),
                )}</span></div>`
              : ""
          }
          ${tags ? `<div class="tree__tags">${tags}</div>` : ""}
          ${
            annotation.source || typeof annotation.confidence === "number"
              ? `<div class="tree__leaf"><span><b>by</b> ${escapeHtml(
                  annotation.source ?? "unknown",
                )}${
                  typeof annotation.confidence === "number"
                    ? ` (${annotation.confidence.toFixed(2)})`
                    : ""
                }</span></div>`
              : ""
          }
          ${annotation.caveat ? `<div class="tree__caveat">${escapeHtml(annotation.caveat)}</div>` : ""}
        </div>`;
    })
    .join("");

  const momentRows = relatedMoments
    .map(
      (moment) => `<div class="tree__leaf">
        <span><span class="tree__span">${escapeHtml(
          `${timecode(moment.start) ?? "0:00"}–${timecode(moment.end) ?? "end"}`,
        )}</span> ${escapeHtml(moment.snippet ?? "")}</span>
      </div>`,
    )
    .join("");

  const annotationNode = `<span class="tree__branch">annotations</span>
    <div class="tree__node">
      ${annotationRows}
      ${
        !annotationRows && momentRows
          ? `<div class="tree__empty">retrieved spans, not yet labelled:</div>${momentRows}`
          : ""
      }
      ${
        !annotationRows && !momentRows
          ? `<div class="tree__empty">not annotated yet — index this clip, then run the curation loop</div>`
          : ""
      }
    </div>`;

  return `<div class="tree">${viewpointNode}${sourceNode}${annotationNode}</div>`;
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

  renderDataset(response.dataset);

  const { analyses, moments } = extractDatalake(response);
  renderDatalake(analyses);
  renderMoments(moments);

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
  dom.datalakePanel.hidden = true;
  dom.momentsPanel.hidden = true;
  dom.datasetPanel.hidden = true;
  state.manifest = null;
  dom.datalake.innerHTML = "";
  dom.moments.innerHTML = "";
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
      addEvent("tool_call", `<b>${escapeHtml(toolLabel(payload.tool ?? "tool"))}</b>`, {
        live: true,
      });
      break;

    case "tool_result": {
      const label = escapeHtml(toolLabel(payload.tool ?? "tool"));
      if (!payload.success) {
        addEvent(
          "tool_fail",
          `<b>${label}</b> failed${payload.error ? ` — ${escapeHtml(payload.error)}` : ""}`,
        );
        break;
      }

      let detail = "";
      if (payload.status === "processing") detail = " — still indexing";
      else if (typeof payload.moments_found === "number") {
        detail = ` — ${payload.moments_found} moments`;
      } else if (payload.videos_found) detail = ` — ${payload.videos_found} videos`;

      addEvent("tool_ok", `<b>${label}</b> done${escapeHtml(detail)}`);
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
  if (state.viewpoint) body.viewpoint = state.viewpoint;
  if (state.minDurationSeconds) {
    body.min_duration_seconds = Number(state.minDurationSeconds);
  }
  if (state.licenseFilter) body.license_filter = state.licenseFilter;
  const targetHours = Number.parseFloat(dom.targetHours.value);
  if (Number.isFinite(targetHours) && targetHours > 0) body.target_hours = targetHours;

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

/* ------------------------------------------------------------ export */

/** Hand the browser a file built from the current manifest. */
const download = (filename, text, mime) => {
  const blob = new Blob([text], { type: mime });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
};

const CSV_COLUMNS = [
  "url",
  "platform",
  "platform_id",
  "title",
  "creator",
  "duration_seconds",
  "viewpoint",
  "viewpoint_confidence",
  "license",
  "usability_score",
  "published_at",
  "datalake_video_id",
];

const csvCell = (value) => {
  if (value === null || value === undefined) return "";
  const text = Array.isArray(value) ? value.join("; ") : String(value);
  return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
};

const exportManifest = (format) => {
  const manifest = state.manifest;
  if (!manifest?.clips?.length) return;

  const stamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-");
  if (format === "jsonl") {
    // One clip per line: what an ingest pipeline reads.
    const body = manifest.clips.map((clip) => JSON.stringify(clip)).join("\n");
    download(`dataset-${stamp}.jsonl`, `${body}\n`, "application/x-ndjson");
    return;
  }

  const header = CSV_COLUMNS.join(",");
  const rows = manifest.clips.map((clip) =>
    CSV_COLUMNS.map((column) => csvCell(clip[column])).join(","),
  );
  download(`dataset-${stamp}.csv`, [header, ...rows].join("\n") + "\n", "text/csv");
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

dom.exportJsonl.addEventListener("click", () => exportManifest("jsonl"));
dom.exportCsv.addEventListener("click", () => exportManifest("csv"));

wireChoiceGroup(dom.viewpoint, "viewpoint", "viewpoint");
wireChoiceGroup(dom.minDuration, "seconds", "minDurationSeconds");
wireChoiceGroup(dom.license, "license", "licenseFilter");
dom.targetHours.addEventListener("change", persistRequirements);

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

  try {
    const saved = JSON.parse(localStorage.getItem(STORAGE_KEY_REQS) ?? "{}");
    const restoreGroup = (container, datasetKey, value) => {
      const chip = [...container.querySelectorAll(".chip")].find(
        (node) => (node.dataset[datasetKey] ?? "") === String(value ?? ""),
      );
      if (!chip) return;
      container.querySelectorAll(".chip").forEach((node) => {
        const active = node === chip;
        node.classList.toggle("is-active", active);
        node.setAttribute("aria-pressed", String(active));
      });
    };
    state.viewpoint = saved.viewpoint ?? "";
    state.minDurationSeconds = saved.minDurationSeconds ?? "";
    state.licenseFilter = saved.licenseFilter ?? "";
    restoreGroup(dom.viewpoint, "viewpoint", state.viewpoint);
    restoreGroup(dom.minDuration, "seconds", state.minDurationSeconds);
    restoreGroup(dom.license, "license", state.licenseFilter);
    if (saved.targetHours) dom.targetHours.value = saved.targetHours;
  } catch {
    /* ignore malformed storage */
  }
};

restore();
checkHealth();
