/** The shell: a sidebar with the product's two halves, and the content beside it.
 *
 * The two views are one flow, not two tools — selecting candidates in the
 * search view queues them for collection, and switching to the second view
 * finds them already in the box.
 */

import { useEffect, useState } from "react";

import { CollectView } from "./components/CollectView";
import { SearchView } from "./components/SearchView";

type View = "search" | "collect";

const API_KEY_STORAGE = "ivs.apiKey";
const THEME_STORAGE = "ivs.theme";
const OWN_KEYS_STORAGE = "ivs.ownKeys";

function readStored(key: string, fallback = ""): string {
  try {
    return localStorage.getItem(key) ?? fallback;
  } catch {
    // Private windows and blocked site data both throw here.
    return fallback;
  }
}

function store(key: string, value: string): void {
  try {
    localStorage.setItem(key, value);
  } catch {
    /* nothing to do; the setting is a convenience */
  }
}

interface Health {
  demo_mode?: boolean;
  auth_required?: boolean;
  model?: string;
  version?: string;
}

/** Keys the viewer brings themselves. Kept in this browser, nowhere else. */
export interface OwnKeys {
  openrouter?: string;
  memories?: string;
  collection?: string;
}

export function App() {
  const [view, setView] = useState<View>("search");
  const [health, setHealth] = useState<Health | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [queued, setQueued] = useState<string[]>([]);
  const [apiKey, setApiKey] = useState(() => readStored(API_KEY_STORAGE));
  const [theme, setTheme] = useState(() => readStored(THEME_STORAGE, "dark"));
  const [ownKeys, setOwnKeys] = useState<OwnKeys>(() => {
    try {
      return JSON.parse(readStored(OWN_KEYS_STORAGE, "{}")) as OwnKeys;
    } catch {
      return {};
    }
  });
  const [keysOpen, setKeysOpen] = useState(false);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    store(THEME_STORAGE, theme);
  }, [theme]);

  useEffect(() => {
    store(API_KEY_STORAGE, apiKey);
  }, [apiKey]);

  useEffect(() => {
    store(OWN_KEYS_STORAGE, JSON.stringify(ownKeys));
  }, [ownKeys]);

  useEffect(() => {
    // Which mode this deployment is in decides what the numbers mean, so it is
    // asked once and said plainly rather than left for the reader to guess.
    let cancelled = false;
    fetch("/api/v1/health")
      .then((response) => (response.ok ? response.json() : null))
      .then((payload) => {
        if (!cancelled && payload) setHealth(payload as Health);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, []);

  const usingOwnKeys = Boolean(ownKeys.openrouter || ownKeys.memories);

  const toggleSelected = (url: string) =>
    setSelected((current) =>
      current.includes(url) ? current.filter((item) => item !== url) : [...current, url],
    );

  return (
    <div className="shell">
      <nav className="sidebar">
        <div className="brand">
          <span className="brand__mark">Internet EgoExo Video Search</span>
          <span className="brand__sub">memories.ai · training-data collection</span>
        </div>

        <div className="nav">
          <button
            type="button"
            className="nav__item"
            aria-current={view === "search"}
            onClick={() => setView("search")}
          >
            <span>1 · Search &amp; scrape</span>
            <small>find footage on the web</small>
          </button>
          <button
            type="button"
            className="nav__item"
            aria-current={view === "collect"}
            onClick={() => setView("collect")}
          >
            <span>2 · Curate &amp; annotate</span>
            <small>
              {selected.length
                ? `${selected.length} clip${selected.length === 1 ? "" : "s"} queued`
                : "index, clean, annotate"}
            </small>
          </button>
        </div>

        <div className="sidebar__footer">
          <div className="field">
            <button
              type="button"
              className="button button--small button--ghost"
              onClick={() => setKeysOpen(!keysOpen)}
            >
              {usingOwnKeys ? "Your keys · no rate limit" : "Use your own keys"}
            </button>
            {keysOpen ? (
              <>
                <span className="sidebar__note">
                  This deployment runs on its owner&apos;s keys and is rate limited.
                  Paste your own to be served without the queue — they stay in this
                  browser, are sent only with your own requests, and are never stored
                  on the server.
                </span>
                <label className="field">
                  <span className="field__label">OpenRouter key</span>
                  <input
                    className="input"
                    type="password"
                    value={ownKeys.openrouter ?? ""}
                    onChange={(event) =>
                      setOwnKeys({ ...ownKeys, openrouter: event.target.value })
                    }
                    placeholder="sk-or-…"
                  />
                </label>
                <label className="field">
                  <span className="field__label">Video Datalake key</span>
                  <input
                    className="input"
                    type="password"
                    value={ownKeys.memories ?? ""}
                    onChange={(event) =>
                      setOwnKeys({ ...ownKeys, memories: event.target.value })
                    }
                    placeholder="sk-mai-…"
                  />
                </label>
                <label className="field">
                  <span className="field__label">Collection id (optional)</span>
                  <input
                    className="input"
                    value={ownKeys.collection ?? ""}
                    onChange={(event) =>
                      setOwnKeys({ ...ownKeys, collection: event.target.value })
                    }
                    placeholder="col_…"
                  />
                </label>
                {usingOwnKeys ? (
                  <button
                    type="button"
                    className="button button--small button--ghost"
                    onClick={() => setOwnKeys({})}
                  >
                    Clear my keys
                  </button>
                ) : null}
              </>
            ) : null}
          </div>
          {health?.auth_required ? (
            // Only when this deployment actually requires one. This is the
            // server's own access key — nothing to do with X/Twitter, which
            // needs no key of its own.
            <label className="field">
              <span className="field__label">Access key for this deployment</span>
              <input
                className="input"
                type="password"
                value={apiKey}
                onChange={(event) => setApiKey(event.target.value)}
                placeholder="required by this server"
              />
            </label>
          ) : null}
          <button
            type="button"
            className="button button--small button--ghost"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          >
            {theme === "dark" ? "Light theme" : "Dark theme"}
          </button>
          <span className="sidebar__note">
            Hand and viewpoint verdicts are read from index captions, not from a hand-tracking
            model.
          </span>
          {health?.model && !health.demo_mode ? (
            <span className="sidebar__note">{health.model}</span>
          ) : null}
        </div>
      </nav>

      <main className="content">
        {health?.demo_mode ? (
          <div className="banner">
            <strong>Demo data.</strong> Every result below is canned — nothing is
            searched, downloaded, indexed or spent. Set <code>OPENROUTER_API_KEY</code>{" "}
            (or <code>GOOGLE_API_KEY</code>) and <code>MEMORIES_API_KEY</code>, and turn{" "}
            <code>DEMO_MODE</code> off, to run it for real.
          </div>
        ) : null}
        {view === "search" ? (
          <SearchView
            apiKey={apiKey}
            ownKeys={ownKeys}
            selected={selected}
            onToggleSelected={toggleSelected}
            onSendToCollection={() => {
              setQueued(selected);
              setView("collect");
            }}
          />
        ) : (
          <CollectView apiKey={apiKey} ownKeys={ownKeys} queuedUrls={queued} />
        )}
      </main>
    </div>
  );
}
