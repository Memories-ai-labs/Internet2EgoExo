/** Drive the whole UI flow in a real browser and report what is wrong.
 *
 * Point it at the stub API (`uv run python ui/qa/stub_api.py 8821`), then:
 *
 *     node ui/qa/flow.mjs ui/qa/shots
 *
 * It walks search -> select -> collect -> gates -> grade -> light theme -> a
 * 420px viewport, screenshots each step, and asserts the things that have
 * actually broken before: the tree must nest and name its levels, the page must
 * not scroll sideways on a phone, a rejected clip must say why, an unmeasured
 * gate must not read as a pass, and the console must stay clean.
 *
 * Needs `npm install playwright` and a Chromium; set PW_CHROMIUM to override
 * the executable path.
 */

import { chromium } from "playwright";

const base = process.env.QA_BASE || "http://127.0.0.1:8821/ui/";
const out = process.argv[2] || ".";
const problems = [];

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

page.on("console", (m) => {
  if (m.type() !== "error") return;
  if (m.location().url.includes("fonts.googleapis.com")) return;
  if (m.text().includes("ERR_CONNECTION_RESET")) return;
  problems.push(`console: ${m.text()} @ ${m.location().url}`);
});
page.on("pageerror", (e) => problems.push(`pageerror: ${e.message}`));
page.on("requestfailed", (r) => {
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

// 3. select and send to collection — two clips, so the batch shows both a clip
// that clears the gates and one that is dropped for having no hands.
await page.locator(".card").first().locator('input[type="checkbox"]').check();
await page.locator(".card").nth(2).locator('input[type="checkbox"]').check();
await page.getByRole("button", { name: "Send to the Datalake" }).click();
await page.waitForSelector(".page-head h1:has-text('Curate')", { timeout: 5000 });
await step("04-collect-prefilled");
const queued = await page.locator(".textarea").inputValue();
if (!queued.includes("aaa1")) problems.push("the selected URL did not reach the collection queue");
if (queued.split("\n").filter(Boolean).length !== 2) {
  problems.push(`the collection queue holds ${queued.split("\n").filter(Boolean).length} URLs, expected 2`);
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
for (const expected of ["G1-HAND", "not measured", "G3-DUP", "anchors"]) {
  if (!gateText.includes(expected)) problems.push(`gate detail missing "${expected}"`);
}

// 6. curate
await page.getByRole("button", { name: "Grade the set" }).click();
await page.waitForSelector(".panel:has-text('Batch grade')", { timeout: 15000 });
await page.waitForTimeout(400);
await step("08-curation");
const curationText = await page.locator(".panel", { hasText: "Curate the set" }).innerText();
for (const expected of ["batch grade", "delivered", "accepted + labelled", "duplicate groups", "0.21h"]) {
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

await browser.close();
console.log(problems.length ? `PROBLEMS:\n- ${problems.join("\n- ")}` : "NO PROBLEMS FOUND");
