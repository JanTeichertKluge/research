// Print a reveal.js deck to PDF with headless Chromium (reveal.js print mode).
// Usage: node print-pdf.cjs <deck.html> <deck.pdf>
const path = require("path");
const { chromium } = require("playwright");

async function main() {
  const [input, output] = process.argv.slice(2);
  if (!input || !output) {
    console.error("usage: node print-pdf.cjs <deck.html> <deck.pdf>");
    process.exit(2);
  }
  const proxy = process.env.HTTPS_PROXY ? { server: process.env.HTTPS_PROXY } : undefined;
  const browser = await chromium.launch({ proxy });
  const page = await browser.newPage();
  const url = "file://" + path.resolve(input) + "?print-pdf";
  await page.goto(url, { waitUntil: "networkidle", timeout: 120000 });
  // Wait until MathJax has typeset every formula.
  await page.waitForFunction(
    () => {
      const mj = window.MathJax;
      if (!mj) return false;
      if (mj.startup && mj.startup.promise) return mj.typesetPromise !== undefined;
      if (mj.Hub) return mj.Hub.queue.pending === 0 && mj.Hub.queue.running === 0;
      return false;
    },
    null,
    { timeout: 120000 }
  );
  await page.waitForTimeout(2000);
  const raw = await page.evaluate(() => {
    const text = document.body.innerText;
    return (text.match(/\\\(|\\\[|\$\$/g) || []).length;
  });
  if (raw > 0) console.warn(`warning: ${raw} untypeset math delimiters remain`);
  await page.pdf({ path: output, preferCSSPageSize: true, printBackground: true });
  await browser.close();
  console.log("written", output);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
