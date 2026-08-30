/** Reading a Server-Sent Event stream from a POST.
 *
 * `EventSource` cannot do this — it is GET-only and cannot set headers — and
 * every streaming endpoint here takes a JSON body and an API key. So the stream
 * is read off `fetch`'s body reader and split by hand.
 *
 * The parsing is deliberately forgiving. A frame that does not parse is
 * dropped rather than killing the stream: the server also emits comment pings
 * to keep the connection alive, and a run that dies because of a keep-alive is
 * worse than one that ignores a frame it did not understand.
 */

/** Blank line between frames; a lone newline separates fields within one. */
const FRAME = /\r?\n\r?\n/;
const LINE = /\r?\n/;

export interface StreamHandlers {
  onEvent: (event: string, data: Record<string, unknown>) => void;
  onError?: (message: string) => void;
  onDone?: () => void;
}

export interface StreamOptions {
  apiKey?: string;
  /** Per-request credentials, when the viewer is bringing their own. */
  keys?: { openrouter?: string; memories?: string; collection?: string };
  signal?: AbortSignal;
}

/** POST `body` to `url` and hand every SSE frame to `handlers.onEvent`. */
export async function streamRequest(
  url: string,
  body: unknown,
  handlers: StreamHandlers,
  options: StreamOptions = {},
): Promise<void> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (options.apiKey) headers["X-API-Key"] = options.apiKey;
  if (options.keys?.openrouter) headers["X-OpenRouter-Key"] = options.keys.openrouter;
  if (options.keys?.memories) headers["X-Memories-Key"] = options.keys.memories;
  if (options.keys?.collection) headers["X-Memories-Collection"] = options.keys.collection;

  let response: Response;
  try {
    response = await fetch(url, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
      signal: options.signal,
    });
  } catch (cause) {
    // An abort is the caller stopping the run on purpose, not a failure, and
    // firing onError for it would paint a red banner over a deliberate stop.
    if ((cause as Error).name === "AbortError") return;
    handlers.onError?.((cause as Error).message || "Request failed");
    handlers.onDone?.();
    return;
  }

  if (!response.ok || !response.body) {
    handlers.onError?.(await readError(response));
    handlers.onDone?.();
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  try {
    for (;;) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const frames = buffer.split(FRAME);
      // The last piece may be half a frame; keep it for the next chunk.
      buffer = frames.pop() ?? "";
      for (const frame of frames) dispatch(frame, handlers);
    }
    if (buffer.trim()) dispatch(buffer, handlers);
  } catch (cause) {
    if ((cause as Error).name !== "AbortError") {
      handlers.onError?.((cause as Error).message || "Stream failed");
    }
  } finally {
    await reader.cancel().catch(() => {});
    handlers.onDone?.();
  }
}

function dispatch(frame: string, handlers: StreamHandlers): void {
  let event = "message";
  const data: string[] = [];
  for (const line of frame.split(LINE)) {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    else if (line.startsWith("data:")) data.push(line.slice(5).trim());
  }
  if (!data.length) return;
  try {
    handlers.onEvent(event, JSON.parse(data.join("\n")));
  } catch {
    // A frame that is not JSON is a ping or a partial write. Ignore it.
  }
}

/** The server's own words for why it refused, when it gave any. */
async function readError(response: Response): Promise<string> {
  try {
    const payload = await response.json();
    if (typeof payload.detail === "string") return payload.detail;
    if (Array.isArray(payload.detail) && payload.detail.length) {
      const first = payload.detail[0];
      return first.msg ? `${(first.loc ?? []).join(".")}: ${first.msg}` : "Invalid request";
    }
    if (payload.message) return payload.message;
  } catch {
    // Not JSON. The status is all there is.
  }
  return `Request failed (${response.status})`;
}
