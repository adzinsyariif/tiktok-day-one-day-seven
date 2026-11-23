// Entry for the make.fun "Day one, day seven" TikTok bounty.
// The video itself is the entry: a short clip about ORBIT DASH, a tiny
// agent-built space dodger, on the day it was made and after a week of
// daily updates. The clip is posted on TikTok and its address goes in
// VIDEO.json; this program's only job is to hand that file to the grader.
//
// It runs on Node 22 with the standard library only, no network, no clock:
// read VIDEO.json from the repository root and copy it to the output
// directory, byte for byte. Outside the grader, MAKEFUN_BOT_DIR and
// MAKEFUN_OUTPUT_DIR stand in for /bot and /output:
//   mkdir -p out && MAKEFUN_BOT_DIR=. MAKEFUN_OUTPUT_DIR=out node main.ts

import { copyFileSync, existsSync, mkdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

const botDir = process.env.MAKEFUN_BOT_DIR ?? "/bot";
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? "/output";

const source = join(botDir, "VIDEO.json");
const target = join(outDir, "VIDEO.json");

if (!existsSync(source)) {
  console.error(`VIDEO.json not found in ${botDir}`);
  process.exit(1);
}

mkdirSync(outDir, { recursive: true });
copyFileSync(source, target);

// The gate only accepts a JSON object naming a TikTok video address, so
// refuse to pass along a file that is not even that shape.
let parsed: unknown;
try {
  parsed = JSON.parse(readFileSync(target, "utf8"));
} catch {
  console.error("VIDEO.json is not valid JSON");
  process.exit(1);
}
if (
  typeof parsed !== "object" ||
  parsed === null ||
  typeof (parsed as { url?: unknown }).url !== "string"
) {
  console.error("VIDEO.json has no url string");
  process.exit(1);
}
