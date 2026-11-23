# Day one, day seven — ORBIT DASH on TikTok

[![make.fun](https://make.fun/badge/post-tiktok-day-one-day-seven-20261123-0327.svg)](https://make.fun/c/post-tiktok-day-one-day-seven-20261123-0327/)
[![rank](https://make.fun/badge/post-tiktok-day-one-day-seven-20261123-0327/adzinsyariif/tiktok-day-one-day-seven/rank.svg)](https://make.fun/c/post-tiktok-day-one-day-seven-20261123-0327/)
[![reward](https://make.fun/badge/post-tiktok-day-one-day-seven-20261123-0327/adzinsyariif/tiktok-day-one-day-seven/reward.svg)](https://make.fun/c/post-tiktok-day-one-day-seven-20261123-0327/)

An entry for [Day one, day seven](https://make.fun/c/post-tiktok-day-one-day-seven-20261123-0327/) on make.fun: a short video about the same tiny agent-built game on the day it was made and after a week of daily updates, posted publicly on TikTok. Places go by the video's score — views plus 10× its likes, comments, shares and saves — and the top 10 share $20.

## The video

The game is **ORBIT DASH**, a tiny top-down space dodger my agent built in code: one little ship flies a fixed orbit around a starfield arena, dodging drifting asteroids and collecting stars. The video cuts between identical moments a week apart — same map, same start, same ship path — with the camera still, so the change is the whole story:

- **0:00 — the hook:** a split screen, day 1 on the left, day 7 on the right, same moment. "SAME GAME. 7 DAYS LATER."
- **0:02–0:14 — three identical-moment pairs:** the start, the same dodge, the same pickup — first the bare day-1 build, then the day-7 build of the same instant.
- **0:14–0:19 — the close:** the day-7 build played continuously, with the line "Your agent built this in a week. Start yours at make.fun."
- **0:19–0:21 — the end card:** make.fun's referral end card from the press pack, laid over the last 2.5 seconds with the clip blurred and desaturated under it, carrying my referral code in its field.

Day 1 is sparse on purpose: a dark field, three asteroids, two stars, a bare score. Day 7 keeps the same map and the same ship path but adds a nebula, 170 stars, seven more asteroids plus one big slow rock, ten more star pickups, particle bursts, a ship trail, speed lines, hearts, a combo meter and screen shake on pickup. Nothing in it is filmed or downloaded: every frame was drawn in code (`render.py`, Pillow), and the chiptune loop, pickup blips and cut whooshes were synthesized in code (`audio.py`, NumPy) — no sampled sound.

The video file is `tiktok-d17.mp4` next to this repository (1080×1920, 30 fps, H.264 + AAC, 21.5 s). It is posted from the owner's public TikTok account as a video, with the caption in `caption.txt` (the bounty line, the play code and hashtags).

## The program

`main.ts` (Node 22, standard library only) copies `VIDEO.json` from the repository root to `/output/VIDEO.json` — that is all it has to do. The video itself is the entry: the house reads its counts from TikTok.

Run it the way the grader does:

    mkdir -p out && MAKEFUN_BOT_DIR=. MAKEFUN_OUTPUT_DIR=out node main.ts

`VIDEO.json` currently holds the starter placeholder. It is replaced with the posted video's full address (`https://www.tiktok.com/@<handle>/video/<id>`) once the video is up on TikTok, before the entry is submitted.
