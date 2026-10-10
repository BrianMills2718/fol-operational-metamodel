// Browser check of visualizer/class-diagram.html against a server rooted at the repository.
// Usage: node tests/e2e/class_diagram_e2e.mjs [base-url]   (default http://127.0.0.1:8000)
// Checks: (1) hierarchy - UniversalQuantification below QuantifiedSentence below Sentence below
// Phrase; (2) click - QuantifiedSentence shows body : Sentence and binding : Binding 0..*;
// (3) tooltips - every visible control and class box shows a tooltip bubble on hover.
// Prints one line per check and `RESULT passed=N failed=M`; exits 1 on any failure.
// Screenshots go to tests/e2e/out/.
import { chromium } from "playwright";
import fs from "fs";

const base = process.argv[2] || "http://127.0.0.1:8000";
const out = new URL("./out/", import.meta.url).pathname;
fs.mkdirSync(out, { recursive: true });
let passed = 0, failed = 0;
const log = (ok, name, detail) => { ok ? passed++ : failed++; console.log(`${ok ? "PASS" : "FAIL"} ${name}: ${detail}`); };

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1500, height: 950 } });
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
await page.goto(`${base}/visualizer/class-diagram.html`);
await page.locator(".gv-node").first().waitFor({ timeout: 20000 });
await page.waitForTimeout(1500);
await page.screenshot({ path: `${out}class-diagram.png` });
log(true, "render", `${await page.locator(".gv-node").count()} class boxes drawn; screenshot ${out}class-diagram.png`);

// 1. Hierarchy: compare vertical centres of the four named boxes.
const box = async (name) => {
  const el = page.locator(".gv-node", { has: page.locator(".gv-label", { hasText: new RegExp(`^${name}$`) }) });
  const b = await el.boundingBox();
  return b ? b.y + b.height / 2 : null;
};
const chain = ["Phrase", "Sentence", "QuantifiedSentence", "UniversalQuantification"];
const ys = [];
for (const n of chain) ys.push(await box(n));
const ordered = ys.every((y, i) => y !== null && (i === 0 || y > ys[i - 1]));
log(ordered, "hierarchy", chain.map((n, i) => `${n} y=${ys[i]?.toFixed(0)}`).join(" > "));

// 2. Click QuantifiedSentence and read the details panel.
await page.locator(".gv-node", { has: page.locator(".gv-label", { hasText: /^QuantifiedSentence$/ }) }).click();
await page.waitForTimeout(300);
const panel = (await page.locator("#details").innerText()).replace(/\s+/g, " ");
const wants = ["QuantifiedSentence", "body : Sentence", "binding : Binding", "0..*", "BindingSequenceForQuantifiedSentence", "QuantificationForSentence", "UniversalQuantification", "ExistentialQuantification"];
const missingText = wants.filter((w) => !panel.includes(w));
log(missingText.length === 0, "click details", missingText.length ? `missing: ${missingText.join(", ")}` : `panel shows ${wants.join(" | ")}`);
await page.screenshot({ path: `${out}class-diagram-selected.png` });

// 3. Tooltips: hover every visible control and class box.
await page.locator("#fit").click();
await page.waitForTimeout(400);
const controls = page.locator("button:visible, select:visible, a:visible, [tabindex='0']:visible");
const n = await controls.count();
const missing = [];
for (let i = 0; i < n; i++) {
  const c = controls.nth(i);
  const name = ((await c.innerText().catch(() => "")) || (await c.getAttribute("aria-label")) || `#${i}`).trim().replace(/\s+/g, " ").slice(0, 40);
  await page.mouse.move(1, 1); await page.waitForTimeout(60);
  // A line hidden under another can't be hovered; keyboard focus is the other way to reach it.
  try { await c.hover({ timeout: 2000 }); } catch { await c.focus(); }
  await page.waitForTimeout(250);
  const own = c.locator(".gv-tip");
  const shown = ((await own.count()) && (await own.isVisible())) || (await page.locator("#tip.on").count() && (await page.locator("#tip").innerText()).trim().length > 5);
  if (!shown) missing.push(name);
}
log(missing.length === 0, "tooltips", `${n} controls hovered, ${n - missing.length} showed a tooltip${missing.length ? "; none on: " + missing.join(" | ") : ""}`);

log(errors.length === 0, "console", errors.length ? errors.join(" | ") : "no page errors");
await browser.close();
console.log(`RESULT passed=${passed} failed=${failed}`);
process.exit(failed ? 1 : 0);
