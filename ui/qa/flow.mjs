/** Drive the whole UI flow in a real browser and report what is wrong.
 *
 * Point it at the stub API (`uv run python ui/qa/stub_api.py 8821`), then:
 *
 *     node ui/qa/flow.mjs ui/qa/shots
 *
 * It walks search -> select -> collect -> gates -> grade -> light theme -> a
 * 420px viewport -> the library, then the two ways out of the flow (Stop, and a
 * second search), screenshots each step, and asserts the things that have
 * actually broken before: the tree must nest and name its levels, the page must
 * not scroll sideways on a phone, a rejected clip must say why, an unmeasured
 * gate must not read as a pass, a stopped run must leave a form you can use
 * again, a second search must not keep the first one's selection, and the
 * console must stay clean.
 *
 * Needs `npm install playwright` and a Chromium; set PW_CHROMIUM to override
 * the executable path. QA_BASE points it at a deployment instead of a laptop,
 * and QA_API_KEY carries that deployment's access key when it requires one.
 */

import { chromium } from "playwright";

const base = process.env.QA_BASE || "http://127.0.0.1:8821/ui/";
const out = process.argv[2] || ".";
// A deployment with API_KEYS set answers 401 to everything but /ui/ and
// /api/v1/health, so the walk would die at the first search. The UI keeps the
// viewer's access key in localStorage and sends it as X-API-Key; seeding it
// before the app loads is the same thing a person typing it into the sidebar
// does, and it is what lets this run against a real host rather than a laptop.
const accessKey = process.env.QA_API_KEY || "";
const problems = [];
// Set while a step deliberately makes a request fail, so the console and
// request-failure watchers do not report the failure the step is asserting.
let expectingFailures = false;

// PW_PROXY (or HTTPS_PROXY) lets this run against a deployed URL from a
// sandbox whose only route out is a proxy. The proxy's CA is trusted by the
// browser's own store, so nothing here weakens certificate checking.
const proxyServer = process.env.PW_PROXY || process.env.HTTPS_PROXY;
const browser = await chromium.launch({
  executablePath: process.env.PW_CHROMIUM || undefined,
  // localhost must bypass it, or a proxied browser cannot reach the local app.
  ...(proxyServer
    ? { proxy: { server: proxyServer, bypass: "localhost,127.0.0.1,::1" } }
    : {}),
});
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
if (accessKey) {
  await page.addInitScript((key) => {
    try {
      localStorage.setItem("ivs.apiKey", key);
    } catch {
      /* a browser with site data blocked; the run will fail loudly at the first search */
    }
  }, accessKey);
}

page.on("console", (m) => {
  if (m.type() !== "error") return;
  if (expectingFailures) return;
  if (m.location().url.includes("fonts.googleapis.com")) return;
  if (m.text().includes("ERR_CONNECTION_RESET")) return;
  problems.push(`console: ${m.text()} @ ${m.location().url}`);
});
page.on("pageerror", (e) => problems.push(`pageerror: ${e.message}`));
page.on("requestfailed", (r) => {
  if (expectingFailures) return;
  // fonts.googleapis.com is unreachable from this sandbox; the fallback stack covers it.
  if (r.url().includes("fonts.googleapis.com")) return;
  // A POST-SSE stream that has delivered its last frame is cancelled by the
  // client; Chromium reports that as ERR_ABORTED. Harmless, and the UI content
  // asserted below proves the frames arrived.
  if (r.failure()?.errorText === "net::ERR_ABORTED") return;
  problems.push(`requestfailed: ${r.url()} ${r.failure()?.errorText}`);
});

const step = async (name) => {
  await page.screenshot({ path: `${out}/${name}.png`, fullPage: true });
  console.log(`--- ${name}`);
};

const noHorizontalScroll = async (name) => {
  const report = await page.evaluate(() => {
    const overflow = document.documentElement.scrollWidth - document.documentElement.clientWidth;
    if (overflow <= 1) return { overflow };
    // Name the widest offender so the fix is not guesswork.
    const limit = document.documentElement.clientWidth;
    const widest = [...document.querySelectorAll("*")]
      .map((node) => ({ sel: node.className || node.tagName, right: node.getBoundingClientRect().right }))
      .filter((entry) => entry.right > limit + 1)
      .sort((a, b) => b.right - a.right)
      .slice(0, 3);
    return { overflow, widest };
  });
  if (report.overflow > 1) {
    problems.push(`${name}: scrolls horizontally by ${report.overflow}px — ${JSON.stringify(report.widest)}`);
  }
};

// domcontentloaded, not networkidle: against a real deployment the network
// never goes idle (fonts, analytics), and the app renders before it would.
await page.goto(base, { waitUntil: "domcontentloaded" });
await page.waitForSelector(".shell", { timeout: 15000 });
await step("01-search-empty");
await noHorizontalScroll("search-empty");
console.log("title:", await page.title());
console.log("theme:", await page.getAttribute("html", "data-theme"));
console.log("nav items:", await page.locator(".nav__item").allInnerTexts());

// 1. run a search
await page.fill(".textarea", "first-person cooking videos, hands visible");
await page.fill('input[placeholder="300"]', "300");
await page.fill('input[placeholder="2"]', "2");
await page.getByRole("button", { name: "YouTube" }).click();
await page.getByRole("button", { name: "Search", exact: true }).click();
await page.waitForSelector(".card", { timeout: 15000 });
await page.waitForTimeout(400);
await step("02-search-results");
await noHorizontalScroll("search-results");

console.log("cards:", await page.locator(".card").count());
const banner = await page.locator(".banner").count();
console.log("demo banner:", banner ? "shown" : "absent");
if (!banner) problems.push("demo mode is on but the page does not say so");
console.log("activity rows:", await page.locator(".activity__row").count());
console.log("dataset stats:", (await page.locator(".panel", { hasText: "Dataset" }).first().locator(".stat").allInnerTexts()).join(" | "));

// 2. open the annotation tree on the first card
await page.locator(".card").first().getByRole("button", { name: "Annotation tree" }).click();
await page.waitForSelector(".card__tree .tree", { timeout: 5000 });
await step("03-annotation-tree");
const treeText = (await page.locator(".card__tree").first().innerText()).toLowerCase();
for (const expected of ["task", "action", "event", "prep-mirepoix", "chop-vegetables", "reposition-grip", "hoi/chop-vegetables/right/move-knife"]) {
  if (!treeText.includes(expected)) problems.push(`tree missing "${expected}"`);
}
if (!treeText.includes("hand-tracking")) problems.push("tree is missing the caption-evidence caveat");
if (!treeText.includes("hand assignment not stated")) problems.push("tree does not mark unstated hand assignment");
// The tree must nest, not just list: an event sits inside an action inside a task.
const depth = await page.locator(".card__tree .tree__node .tree__node .tree__node").count();
if (!depth) problems.push("the annotation tree is flat — task/action/event are not nested");

// 3. Select all, then send to collection. Selecting everything is what a real
// run does, and it is also how the queue-longer-than-the-server-cap path gets
// exercised.
await page.getByRole("button", { name: "Select all" }).click();
// Target the Candidates panel by its own title: `hasText` alone also matches
// panels that merely mention the word.
const candidatesPanel = page.locator('.panel:has(.panel__title:text-is("Candidates"))');
const selectedLabel = await candidatesPanel.locator(".panel__meta").innerText();
if (!/\d+ of \d+ selected/.test(selectedLabel)) {
  problems.push(`select all did not report a count: "${selectedLabel}"`);
}
if (!(await page.getByRole("button", { name: "Clear" }).count())) {
  problems.push("Select all did not turn into Clear");
}
// Drop one so the batch contains both an accepted and a rejected clip.
await page.locator(".card").nth(1).locator('input[type="checkbox"]').uncheck();
await page.getByRole("button", { name: "Send to the Datalake" }).click();
await page.waitForSelector(".page-head h1:has-text('Curate')", { timeout: 5000 });
await step("04-collect-prefilled");
const queued = await page.locator(".textarea").inputValue();
if (!queued.includes("aaa1")) problems.push("the selected URL did not reach the collection queue");
if (queued.split("\n").filter(Boolean).length !== 2) {
  problems.push(`the collection queue holds ${queued.split("\n").filter(Boolean).length} URLs, expected 2`);
}
// The label must state the server's real cap, not a hardcoded number.
const urlLabel = await page.locator(".field__label").filter({ hasText: "Candidate URLs" }).innerText();
if (!/indexes \d+ per request/.test(urlLabel)) {
  problems.push(`the URL field does not state the server cap: "${urlLabel}"`);
}

// 4. collect
await page.getByRole("button", { name: "Download & index" }).click();
await page.waitForSelector(".journey__stage--current", { timeout: 10000 });
await step("05-collect-running");
await page.waitForSelector(".pill--pass", { timeout: 20000 });
await page.waitForTimeout(600);
await step("06-collect-done");
console.log("clips:", await page.locator(".clip").count());
const clipText = await page.locator(".clip").first().innerText();
for (const expected of ["accepted", "grade B", "L3", "hands"]) {
  if (!clipText.includes(expected)) problems.push(`clip summary missing "${expected}"`);
}
if (!(await page.locator(".clip", { hasText: "no hands visible" }).count())) {
  problems.push("the rejected clip is not shown with its reason");
}

// 5. gates + tree detail
await page.locator(".clip").first().getByRole("button", { name: "Gates & annotation tree" }).click();
await page.waitForSelector(".gates", { timeout: 5000 });
await step("07-gates");
const gateText = await page.locator(".clip").first().innerText();
for (const expected of ["G1-HAND", "not measured", "anchors"]) {
  if (!gateText.includes(expected)) problems.push(`gate detail missing "${expected}"`);
}

// 6. curate
await page.getByRole("button", { name: "Grade the set" }).click();
await page.waitForSelector(".panel:has-text('Batch grade')", { timeout: 15000 });
await page.waitForTimeout(400);
await step("08-curation");
const curationText = await page.locator(".panel", { hasText: "Curate the set" }).innerText();
for (const expected of ["batch grade", "delivered", "accepted + labelled", "0.21h"]) {
  if (!curationText.toLowerCase().includes(expected)) problems.push(`curation panel missing "${expected}"`);
}
await noHorizontalScroll("curation");

// 7. light theme
await page.getByRole("button", { name: "Light theme" }).click();
await page.waitForTimeout(300);
await step("09-light-theme");
const bg = await page.evaluate(() => getComputedStyle(document.body).backgroundColor);
if (bg !== "rgb(255, 255, 255)") problems.push(`light theme body background is ${bg}`);

// 8. narrow viewport
await page.setViewportSize({ width: 420, height: 900 });
await page.waitForTimeout(300);
await step("10-narrow");
await noHorizontalScroll("narrow");

// 9. the library — the clean clips, footage from the Datalake and tree from the
// store, joined on the video id. Asserted against whatever the server actually
// holds rather than a fixture: the point of this view is that it shows the real
// corpus, so a hard-coded expectation would pass on an empty one.
await page.setViewportSize({ width: 1280, height: 900 });
await page.getByRole("button", { name: /Library/ }).click();
await page.waitForSelector(".library", { timeout: 15000 });
await page.waitForTimeout(600);
await step("11-library");

const libraryText = await page.locator(".library").innerText();
for (const expected of ["clips", "action anchors", "viewpoint"]) {
  // Case-insensitive: the stat labels render through text-transform, and
  // innerText reports the rendered text, not the source.
  if (!libraryText.toLowerCase().includes(expected)) {
    problems.push(`library missing the "${expected}" total`);
  }
}

const rows = await page.locator(".clipRow").count();
const emptyNote = await page.locator(".library__note").count();
if (rows === 0 && emptyNote === 0) {
  problems.push("the library shows neither clips nor an explanation of why it is empty");
}

if (rows > 0) {
  // Provenance on every row: a clip nobody can trace back is a clip that fails
  // G0-PROV, and the row is where a person would notice.
  const firstSource = await page.locator(".clipRow__source").first().innerText();
  if (!/from \w+/.test(firstSource)) {
    problems.push(`a library row does not say where the clip came from: "${firstSource}"`);
  }

  await page.locator(".clipRow").first().click();
  await page.waitForSelector(".ltree", { timeout: 15000 });
  await page.waitForTimeout(500);
  await step("12-library-clip");
// Objects are the facet a buyer reaches for first, and they were being dropped
// on the way into the store — so assert they reach the page, and that clicking
// one filters by it.
const clipText = await page.locator(".ltree").innerText();
if (!clipText.toLowerCase().includes("metal bowl")) {
  problems.push("library clip is missing its objects");
}

  const treeNodes = await page.locator(".ltree__node").count();
  if (!treeNodes) problems.push("the opened clip shows no annotation tree");

  // An unlabelled span must read as unlabelled rather than as a blank row —
  // these clips were cut and cleaned before anything labelled them.
  const spans = await page.locator(".ltree__span").allInnerTexts();
  if (spans.some((text) => !/\d/.test(text))) {
    problems.push(`a tree node has no timespan: ${JSON.stringify(spans)}`);
  }
  const labels = await page.locator(".ltree__label").allInnerTexts();
  if (labels.some((text) => !text.trim())) {
    problems.push("a tree node renders an empty label instead of saying unlabelled");
  }
}

// The search box must filter rather than decorate.
await page.locator("input[type=search]").fill("zzz-nothing-matches-this");
await page.waitForTimeout(900);
const afterSearch = await page.locator(".clipRow").count();
if (afterSearch !== 0) {
  problems.push(`searching for nonsense still shows ${afterSearch} clip(s)`);
}
await step("13-library-search-empty");
await noHorizontalScroll("library");

await page.setViewportSize({ width: 420, height: 900 });
await page.waitForTimeout(300);
await step("14-library-narrow");
await noHorizontalScroll("library-narrow");

// 10. Stopping a run, and what a second search does to the first one's
// selection. Both are dead ends a person reaches by accident rather than by
// following the flow, and both were real: Stop left the form saying
// "Searching…" with no way back, and a stale selection was still queued for
// download after the clips it named had left the screen.
await page.setViewportSize({ width: 1280, height: 900 });
await page.goto(base, { waitUntil: "domcontentloaded" });
await page.waitForSelector(".shell", { timeout: 15000 });

// A server that has not answered yet, so Stop lands before the first byte —
// which is the case the abort path used to swallow.
const stall = "**/api/v1/queries/stream";
await page.route(stall, async (route) => {
  await new Promise((resolve) => setTimeout(resolve, 6000));
  await route.fulfill({ status: 200, contentType: "text/event-stream", body: "" }).catch(() => {});
});
await page.getByRole("button", { name: "Search", exact: true }).click();
await page.waitForSelector("button:has-text('Stop')", { timeout: 5000 });
await page.getByRole("button", { name: "Stop" }).click();
await page.waitForTimeout(600);
await step("15-stopped");
const idle = page.getByRole("button", { name: "Search", exact: true });
if (!(await idle.count()) || !(await idle.isEnabled())) {
  problems.push("after Stop the search form is still busy — the run cannot be started again");
}
await page.unroute(stall);

await page.goto(base, { waitUntil: "domcontentloaded" });
await page.waitForSelector(".shell", { timeout: 15000 });
await page.getByRole("button", { name: "Search", exact: true }).click();
await page.waitForSelector(".card", { timeout: 15000 });
await page.getByRole("button", { name: "Select all" }).click();

// The same endpoint, with the ids rewritten: a second search over a different
// corpus, which is exactly when a carried-over selection does damage.
await page.route(stall, async (route) => {
  const response = await route.fetch();
  const body = (await response.text())
    .replaceAll("aaa1", "zzz9")
    .replaceAll("bbb2", "yyy8")
    .replaceAll("ccc3", "xxx7");
  await route.fulfill({ response, body });
});
await page.fill(".textarea", "a second query, over other footage");
await page.getByRole("button", { name: "Search", exact: true }).click();
await page.waitForSelector(".card", { timeout: 15000 });
await page.waitForTimeout(400);
await step("16-second-search");

const candidates = page.locator('.panel:has(.panel__title:text-is("Candidates"))');
const afterSecond = await candidates.locator(".panel__meta").innerText();
const stillChecked = await page.locator(".card input[type=checkbox]:checked").count();
if (/selected/.test(afterSecond) && stillChecked === 0) {
  problems.push(`a second search kept the first one's selection: "${afterSecond}" with nothing on screen selected`);
}
if (!(await page.getByRole("button", { name: "Send to the Datalake" }).isDisabled()) && stillChecked === 0) {
  problems.push("a second search leaves clips queued for the Datalake that are no longer on screen");
}
await page.unroute(stall);

// 11. A library nobody is allowed to read must say so. Every clips endpoint
// sits behind the deployment's access key, and a 401 body is valid JSON — so a
// locked shelf used to render as `0 matches`, indistinguishable from a corpus
// that really is empty. Asserted with an injected 401 rather than by unsetting
// the key, so it holds whether or not this run has one.
expectingFailures = true;
await page.route("**/api/v1/clips**", (route) =>
  route.fulfill({
    status: 401,
    contentType: "application/json",
    body: JSON.stringify({ detail: "Missing X-API-Key header" }),
  }),
);
await page.goto(base, { waitUntil: "domcontentloaded" });
await page.waitForSelector(".shell", { timeout: 15000 });
await page.getByRole("button", { name: /Library/ }).click();
await page.waitForSelector(".library", { timeout: 15000 });
await page.waitForTimeout(800);
await step("17-library-locked");
const lockedText = await page.locator(".library").innerText();
if (!/x-api-key|unauthorized|401|could not read/i.test(lockedText)) {
  problems.push(`a 401 from the clips endpoints renders as an empty library: "${lockedText.slice(0, 160).replace(/\n/g, " / ")}"`);
}
await page.unroute("**/api/v1/clips**");
expectingFailures = false;

await browser.close();
console.log(problems.length ? `PROBLEMS:\n- ${problems.join("\n- ")}` : "NO PROBLEMS FOUND");
