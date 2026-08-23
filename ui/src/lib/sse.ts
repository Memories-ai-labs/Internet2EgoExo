/** POST a request and read its Server-Sent Events back frame by frame.
 *
 * `EventSource` cannot POST, and every stream here needs a body — so this is
 * fetch plus a small SSE parser. Runs take minutes, so the caller sees each
 * frame as it lands rather than a spinner and then everything at once.
 */

const FRAME = /\r?\n\r?\n/;
const LINE = /\r?\n/;

export interface StreamHandlers {
  onEvent: (event: string, data: Record<string, unknown>) => void;
  onError?: (message: string) => void;
  /** Always called once a run is over — completed, failed or aborted. */
  onDone?: () => void;
}

export interface StreamOptions {
  /** This deployment's access key, when it requires one. */
  apiKey?: string;
  /** Keys the viewer brought themselves. Sent with their own requests only. */
  keys?: { openrouter?: string; memories?: string; collection?: string };
  signal?: AbortSignal;
}

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
  } catch (error) {
    // An abort before the first byte is the Stop button, not a failure: no
    // error to report — but the run is over, and the caller has to be told, or
    // the form it is driving stays "Searching…" with no way back.
    if ((error as Error).name === "AbortError") {
      handlers.onDone?.();
      return;
    }
    handlers.onError?.((error as Error).message || "Request failed");
    handlers.onDone?.();
    return;
  }

  if (!response.ok || !response.body) {
    handlers.onError?.(await errorText(response));
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
      buffer = frames.pop() ?? "";
      for (const frame of frames) dispatch(frame, handlers);
    }
    if (buffer.trim()) dispatch(buffer, handlers);
  } catch (error) {
    // Same again mid-stream: an abort is what Stop does, not something to
    // report as a failure.
    if ((error as Error).name !== "AbortError") {
      handlers.onError?.((error as Error).message || "Stream failed");
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
    const payload = JSON.parse(data.join("\n")) as Record<string, unknown>;
    handlers.onEvent(event, payload);
  } catch {
    /* a half-written frame is not worth failing a run over */
  }
}

/** Whatever the server said went wrong, in the shape FastAPI says it. */
async function errorText(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as {
      detail?: string | Array<{ loc?: string[]; msg?: string }>;
      message?: string;
    };
    if (typeof payload.detail === "string") return payload.detail;
    if (Array.isArray(payload.detail) && payload.detail.length) {
      const first = payload.detail[0];
      return first.msg ? `${(first.loc ?? []).join(".")}: ${first.msg}` : "Invalid request";
    }
    if (payload.message) return payload.message;
  } catch {
    /* not JSON; the status is all there is */
  }
  return `Request failed (${response.status})`;
}
