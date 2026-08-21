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

export function App() {
  const [view, setView] = useState<View>("search");
  const [selected, setSelected] = useState<string[]>([]);
  const [queued, setQueued] = useState<string[]>([]);
  const [apiKey, setApiKey] = useState(() => readStored(API_KEY_STORAGE));
  const [theme, setTheme] = useState(() => readStored(THEME_STORAGE, "dark"));

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    store(THEME_STORAGE, theme);
  }, [theme]);

  useEffect(() => {
    store(API_KEY_STORAGE, apiKey);
  }, [apiKey]);

  const toggleSelected = (url: string) =>
    setSelected((current) =>
      current.includes(url) ? current.filter((item) => item !== url) : [...current, url],
    );

  return (
    <div className="shell">
      <nav className="sidebar">
        <div className="brand">
          <span className="brand__mark">Internet Video Search</span>
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
          <label className="field">
            <span className="field__label">API key — only if the server sets one</span>
            <input
              className="input"
              type="password"
              value={apiKey}
              onChange={(event) => setApiKey(event.target.value)}
              placeholder="X-API-Key"
            />
          </label>
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
        </div>
      </nav>

      <main className="content">
        {view === "search" ? (
          <SearchView
            apiKey={apiKey}
            selected={selected}
            onToggleSelected={toggleSelected}
            onSendToCollection={() => {
              setQueued(selected);
              setView("collect");
            }}
          />
        ) : (
          <CollectView apiKey={apiKey} queuedUrls={queued} />
        )}
      </main>
    </div>
  );
}
