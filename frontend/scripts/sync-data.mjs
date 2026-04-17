// Copy the Parquet snapshot and prediction CSVs into the frontend so they're
// bundled by Next.js. Vercel's build VM cannot follow `../` outside this
// project root, so we copy from `../data/` and `../outputs/` into
// `./data/` and `./data/predictions/` before `next dev` or `next build`.
//
// Wired via `predev` and `prebuild` scripts in package.json.

import { mkdir, copyFile, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const FRONTEND = path.resolve(path.dirname(__filename), "..");
const REPO = path.resolve(FRONTEND, "..");

const COPIES = [
  {
    src: path.join(REPO, "data", "dashboard_wide.parquet"),
    dst: path.join(FRONTEND, "data", "dashboard_wide.parquet"),
    required: true,
  },
  {
    src: path.join(REPO, "outputs", "forecast_predictions.csv"),
    dst: path.join(FRONTEND, "data", "predictions", "forecast_predictions.csv"),
    required: true,
  },
  {
    src: path.join(REPO, "outputs", "anomaly_predictions.csv"),
    dst: path.join(FRONTEND, "data", "predictions", "anomaly_predictions.csv"),
    required: true,
  },
];

async function copyOne({ src, dst, required }) {
  try {
    await stat(src);
  } catch {
    const msg = `missing source: ${src}`;
    if (required) {
      console.error(`error: ${msg}`);
      process.exitCode = 1;
      return;
    }
    console.warn(`warn: ${msg} (skipping)`);
    return;
  }
  await mkdir(path.dirname(dst), { recursive: true });
  await copyFile(src, dst);
  const { size } = await stat(dst);
  console.log(`copied ${path.relative(FRONTEND, dst)} (${(size / 1_000_000).toFixed(1)} MB)`);
}

await Promise.all(COPIES.map(copyOne));
