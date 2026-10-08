# Measurement scripts

One-off recon/QA scripts used while measuring the original site. They are not part of the build.
They need browser tooling that is deliberately **not** in `package.json` (a fresh `npm ci` would otherwise
download a full Chromium just to build the site):

```bash
npm install --no-save puppeteer jsdom node-fetch
node scripts/measure/run-measurements.mjs
```
