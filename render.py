# render.py — renders every frame of the ORBIT DASH TikTok video in code.
# Game: a tiny top-down space dodger. A little ship flies one fixed orbit
# around a starfield arena, dodging drifting asteroids and collecting stars.
# Day 1 and day 7 share the same map, the same start and the same ship path;
# day 7 just has visibly more going on: more asteroids, more stars, particles,
# a trail, speed lines, a full HUD, nebula, screen shake on pickup.
# No camera footage, no stock media: every pixel is drawn here with Pillow.
#
# Timeline (30 fps, 1080x1920, 21.5 s total):
#   0.0- 2.0  HOOK split screen: DAY 1 | DAY 7, same moment
#   2.0- 4.0  pair 1, DAY 1: the start        4.0- 6.0  pair 1, DAY 7
#   6.0- 8.0  pair 2, DAY 1: the same dodge  8.0-10.0  pair 2, DAY 7
#  10.0-12.0  pair 3, DAY 1: the same pickup 12.0-14.0  pair 3, DAY 7
#  14.0-21.5  closing: DAY 7 played continuously, invite lines
# The end card is laid over the last 2.5 s later, in ffmpeg (see assemble step).

import math
import os
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1080, 1920
FPS = 30
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "work", "frames")
os.makedirs(OUT, exist_ok=True)

FONT_BIG = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(px):
    return ImageFont.truetype(FONT_BIG, px)


# ---------------------------------------------------------------- game model
CX, CY = 540, 940          # arena centre (ship orbit centre)
RX, RY = 330, 500          # ship orbit radii
PERIOD = 7.0               # one orbit every 7 s


def ship_pos(tau):
    th = 2 * math.pi * tau / PERIOD
    wob = 1 + 0.06 * math.sin(2 * math.pi * tau / 3.5)
    return (CX + RX * wob * math.cos(th), CY + RY * wob * math.sin(th))


def ship_vel(tau):
    p0 = ship_pos(tau)
    p1 = ship_pos(tau + 0.05)
    return (p1[0] - p0[0], p1[1] - p0[1])


# Base asteroids: same in both versions. Each is (x0, y0, vx, vy, radius).
BASE_ASTEROIDS = [
    (200, 500, 26, 14, 46),
    (880, 620, -22, 20, 58),
    (540, 1560, 10, -26, 40),
]
# Extra asteroids only day 7 gets (same map, more going on).
EXTRA_ASTEROIDS = [
    (120, 900, 34, -8, 34),
    (960, 1250, -30, -12, 44),
    (700, 340, -16, 26, 30),
    (330, 1400, 24, -18, 52),
    (980, 800, -36, 6, 28),
    (90, 1500, 30, -22, 38),
    (620, 700, -12, -30, 26),
]
# One big slow rock day 7 only, crossing near the ship's path.
BIG_ASTEROID = (1080, 300, -14, 30, 84)


def asteroid_pos(a, tau):
    x0, y0, vx, vy, r = a
    x = 60 + ((x0 - 60 + vx * tau) % 960)
    y = 320 + ((y0 - 320 + vy * tau) % 1420)
    return (x, y, r)


# Star pickups: placed exactly on the ship's path so the ship collects them
# at known game times. Star A is the "same pickup" moment (tau 8.6).
PICKUP_TIMES = [5.1, 8.6, 11.2, 15.0]
STAR_SPOTS = [ship_pos(t) for t in PICKUP_TIMES]
# Extra stars day 7 only, scattered around the arena.
EXTRA_STARS = [(240, 700), (840, 1080), (420, 480), (760, 1500),
               (150, 1150), (950, 420), (540, 620), (300, 1620),
               (880, 1620), (660, 1240)]


def star_state(tau):
    """Return list of (x, y, collected, burst_age) for the 4 path stars."""
    out = []
    for i, (t_pick, (sx, sy)) in enumerate(zip(PICKUP_TIMES, STAR_SPOTS)):
        if tau < t_pick:
            out.append((sx, sy, False, None))
        elif tau < t_pick + 0.9:
            out.append((sx, sy, True, tau - t_pick))
        elif tau < t_pick + 1.6:
            out.append((sx, sy, True, None))  # gone, respawning
        else:
            out.append((sx, sy, False, None))  # back again
    return out


def score_at(tau, rich):
    n = sum(1 for t in PICKUP_TIMES if tau >= t)
    return n if not rich else n * 100 + (25 if n else 0)


# ---------------------------------------------------------------- backgrounds
def make_bg(rich):
    img = Image.new("RGB", (W, H), (8, 10, 24) if not rich else (10, 8, 32))
    d = ImageDraw.Draw(img, "RGBA")
    rng = random.Random(7)
    if rich:
        # Soft nebula blobs: purple, teal, magenta, very low alpha.
        neb = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        nd = ImageDraw.Draw(neb)
        for (x, y, r, col) in [(220, 500, 420, (120, 60, 200)),
                               (900, 1200, 480, (30, 140, 160)),
                               (600, 1700, 380, (200, 60, 140)),
                               (800, 350, 300, (90, 80, 220))]:
            nd.ellipse([x - r, y - r, x + r, y + r], fill=col + (26,))
        neb = neb.filter(ImageFilter.GaussianBlur(90))
        img = Image.alpha_composite(img.convert("RGBA"), neb).convert("RGB")
        d = ImageDraw.Draw(img, "RGBA")
    nstars = 46 if not rich else 170
    for _ in range(nstars):
        x = rng.randint(20, W - 20)
        y = rng.randint(300, H - 60)
        r = rng.choice([1, 1, 2, 2, 3])
        a = rng.randint(90, 220) if rich else rng.randint(50, 130)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 255, a))
    # Faint arena frame.
    d.rectangle([48, 300, W - 48, H - 48], outline=(255, 255, 255, 26), width=2)
    return img


BG_D1 = make_bg(False)
BG_D7 = make_bg(True)


# ---------------------------------------------------------------- drawing bits
def draw_asteroid(d, x, y, r, rich):
    d.ellipse([x - r, y - r, x + r, y + r], fill=(96, 88, 104, 255),
              outline=(170, 160, 180, 255), width=3)
    d.ellipse([x - r * 0.45, y - r * 0.3, x - r * 0.05, y + r * 0.1],
              fill=(70, 64, 78, 255))
    d.ellipse([x + r * 0.15, y + r * 0.35, x + r * 0.5, y + r * 0.65],
              fill=(70, 64, 78, 255))
    if rich:
        d.ellipse([x - r, y - r, x + r, y + r], outline=(255, 190, 120, 90), width=2)


def draw_star(d, x, y, r, glow):
    if glow:
        for rr, a in [(r * 2.6, 40), (r * 1.9, 80), (r * 1.4, 130)]:
            d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(255, 210, 80, a))
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((x + rr * math.cos(ang), y + rr * math.sin(ang)))
    d.polygon(pts, fill=(255, 214, 90, 255), outline=(255, 240, 170, 255))


def draw_ship(d, x, y, vx, vy, rich, tau):
    ang = math.atan2(vy, vx)
    L, Sw = 46, 30
    nose = (x + L * math.cos(ang), y + L * math.sin(ang))
    left = (x + Sw * math.cos(ang + 2.5), y + Sw * math.sin(ang + 2.5))
    right = (x + Sw * math.cos(ang - 2.5), y + Sw * math.sin(ang - 2.5))
    back = (x - L * 0.55 * math.cos(ang), y - L * 0.55 * math.sin(ang))
    # Engine flame, flickering with time.
    fl = 26 + 10 * math.sin(tau * 22)
    tip = (x - (L * 0.55 + fl) * math.cos(ang), y - (L * 0.55 + fl) * math.sin(ang))
    d.polygon([left, tip, right], fill=(255, 150, 40, 220))
    d.polygon([nose, left, back, right], fill=(120, 220, 255, 255),
              outline=(255, 255, 255, 255))
    d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=(255, 255, 255, 255))


def burst_particles(d, cx, cy, age, seed):
    rng = random.Random(seed)
    for _ in range(26):
        ang = rng.uniform(0, 2 * math.pi)
        spd = rng.uniform(120, 420)
        life = 1 - age / 0.9
        px = cx + math.cos(ang) * spd * age
        py = cy + math.sin(ang) * spd * age
        r = max(2, 7 * life)
        col = rng.choice([(255, 210, 90), (255, 120, 200), (140, 220, 255)])
        d.ellipse([px - r, py - r, px + r, py + r],
                  fill=col + (int(255 * life),))


def pill(d, x, y, text, fg, bg, px=64):
    f = font(px)
    bb = d.textbbox((0, 0), text, font=f)
    w, h = bb[2] - bb[0] + 56, bb[3] - bb[1] + 36
    d.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, fill=bg)
    d.text((x + 28, y + 14), text, font=f, fill=fg)
    return w, h


def outlined_text(d, xy, text, f, fill, outline=(10, 10, 20, 255), ow=4):
    x, y = xy
    for dx in range(-ow, ow + 1, 2):
        for dy in range(-ow, ow + 1, 2):
            d.text((x + dx, y + dy), text, font=f, fill=outline)
    d.text((x, y), text, font=f, fill=fill)


def center_text(d, y, text, px, fill=(255, 255, 255, 255)):
    f = font(px)
    bb = d.textbbox((0, 0), text, font=f)
    w = bb[2] - bb[0]
    outlined_text(d, ((W - w) // 2, y), text, f, fill)


# ---------------------------------------------------------------- one frame
def render_frame(tau, rich, day_label=None, caption=None, title=None, clean=False):
    """Draw one gameplay frame at game time tau. rich=False is the day-1 build.
    clean=True skips the HUD and bottom line (for the split-screen hook and
    the closing, where big text sits over the frame instead)."""
    img = (BG_D7 if rich else BG_D1).copy()
    d = ImageDraw.Draw(img, "RGBA")

    # Screen shake on day 7 for a quarter second after a pickup.
    shx, shy = 0, 0
    if rich:
        for t_pick in PICKUP_TIMES:
            if 0 <= tau - t_pick < 0.25:
                rng = random.Random(int(t_pick * 10))
                shx = rng.randint(-7, 7)
                shy = rng.randint(-7, 7)

    # Extra stars (day 7 only) + path stars.
    if rich:
        for (sx, sy) in EXTRA_STARS:
            tw = 0.75 + 0.25 * math.sin(tau * 3 + sx)
            draw_star(d, sx + shx, sy + shy, 15 * tw, glow=True)
    for i, (sx, sy, collected, age) in enumerate(star_state(tau)):
        if not collected:
            draw_star(d, sx + shx, sy + shy, 20, glow=rich)
        elif rich and age is not None:
            burst_particles(d, sx + shx, sy + shy, age, seed=100 + i)

    # Asteroids: same 3 in both, 7 more + 1 big one on day 7.
    asts = list(BASE_ASTEROIDS)
    if rich:
        asts += EXTRA_ASTEROIDS
        asts.append(BIG_ASTEROID)
    for a in asts:
        x, y, r = asteroid_pos(a, tau)
        draw_asteroid(d, x + shx, y + shy, r, rich)

    # Ship trail (day 7 only), then the ship.
    sx, sy = ship_pos(tau)
    vx, vy = ship_vel(tau)
    if rich:
        trail = [ship_pos(tau - k * 0.03) for k in range(14, 0, -1)]
        for k, (tx, ty) in enumerate(trail):
            a = int(140 * k / len(trail))
            d.line([(trail[j][0], trail[j][1]) for j in range(k + 1)],
                   fill=(120, 220, 255, a), width=5)
        # Speed lines near the frame edges.
        rng = random.Random(3)
        for _ in range(10):
            ex = rng.randint(60, W - 60)
            ey = rng.randint(320, H - 80)
            ln = rng.randint(40, 110)
            d.line([ex, ey, ex + ln * vx / 300, ey + ln * vy / 300],
                   fill=(255, 255, 255, 70), width=3)
    draw_ship(d, sx + shx, sy + shy, vx, vy, rich, tau)

    # HUD (skipped in clean mode, where big text covers the frame instead).
    sc = score_at(tau, rich)
    if rich and not clean:
        pill(d, 60, 340, f"SCORE {sc}", (20, 20, 30, 255), (255, 255, 255, 235), 58)
        # Hearts top right.
        for i in range(3):
            hx, hy = W - 110 - i * 78, 372
            d.ellipse([hx - 26, hy - 26, hx + 26, hy + 26], fill=(255, 80, 120, 255))
        # Combo bar under the score.
        n = sum(1 for t in PICKUP_TIMES if tau >= t)
        d.rounded_rectangle([60, 440, 460, 470], radius=15, fill=(255, 255, 255, 70))
        d.rounded_rectangle([60, 440, 60 + 400 * min(n, 4) / 4, 470], radius=15,
                            fill=(255, 210, 90, 255))
        d.text((60, 486), f"COMBO x{max(n, 1)}", font=font(44),
               fill=(255, 210, 90, 255))
        d.text((60, H - 130), "LEVEL 7 — 7 days of updates", font=font(46),
               fill=(255, 255, 255, 220)) if not clean else None
    elif not clean:
        d.text((60, 350), f"SCORE {sc}", font=font(54), fill=(255, 255, 255, 200))
        d.text((60, H - 130), "no upgrades yet", font=font(46),
               fill=(255, 255, 255, 150))

    # Day pill top centre.
    if day_label:
        f = font(62)
        bb = d.textbbox((0, 0), day_label, font=f)
        w = bb[2] - bb[0] + 60
        d.rounded_rectangle([(W - w) // 2, 96, (W + w) // 2, 96 + 96],
                            radius=48, fill=(196, 28, 131, 255))
        d.text(((W - (bb[2] - bb[0])) // 2, 112), day_label, font=f,
               fill=(255, 255, 255, 255))
    if caption:
        center_text(d, H - 330, caption, 58, (255, 255, 255, 255))
    if title:
        center_text(d, 330, title[0], 96)
        center_text(d, 450, title[1], 96)
    return img


def render_split(tau):
    """Hook frame: day 1 on the left half, day 7 on the right, same moment."""
    left = render_frame(tau, False, clean=True).crop((0, 0, W // 2, H))
    right = render_frame(tau, True, clean=True).crop((W // 2, 0, W, H))
    img = Image.new("RGB", (W, H))
    img.paste(left, (0, 0))
    img.paste(right, (W // 2, 0))
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([W // 2 - 5, 0, W // 2 + 5, H], fill=(255, 255, 255, 255))
    center_text(d, 330, "SAME GAME.", 92)
    center_text(d, 450, "7 DAYS LATER.", 92)
    f = font(64)
    for cx, lab in [(W // 4, "DAY 1"), (3 * W // 4, "DAY 7")]:
        bb = d.textbbox((0, 0), lab, font=f)
        w = bb[2] - bb[0] + 56
        d.rounded_rectangle([cx - w // 2, 1580, cx + w // 2, 1580 + 92],
                            radius=46, fill=(0, 0, 0, 160))
        d.text((cx - (bb[2] - bb[0]) // 2, 1596), lab, font=f,
               fill=(255, 255, 255, 255))
    return img


# ---------------------------------------------------------------- timeline
# (kind, game-time start, duration, rich, day label, caption)
SEGMENTS = [
    ("split", 2.0, 2.0, None, None, None),
    ("game", 0.0, 2.0, False, "DAY 1", "the same start"),
    ("game", 0.0, 2.0, True, "DAY 7", "the same start"),
    ("game", 4.0, 2.0, False, "DAY 1", "the same dodge"),
    ("game", 4.0, 2.0, True, "DAY 7", "the same dodge"),
    ("game", 8.0, 2.0, False, "DAY 1", "the same pickup"),
    ("game", 8.0, 2.0, True, "DAY 7", "the same pickup"),
    ("game", 10.0, 7.5, True, "DAY 7", None),
]
TOTAL_S = sum(s[2] for s in SEGMENTS)


def closing_text(d, local_t):
    """Invite lines over the closing day-7 play."""
    if local_t < 3.2:
        center_text(d, 250, "Your agent built this", 84)
        center_text(d, 360, "in a week.", 84)
    else:
        center_text(d, 250, "Start yours", 84)
        center_text(d, 360, "at make.fun", 84)


def main():
    n = 0
    for kind, t0, dur, rich, label, caption in SEGMENTS:
        frames = int(round(dur * FPS))
        for i in range(frames):
            tau = t0 + i / FPS
            if kind == "split":
                img = render_split(tau)
            else:
                # Closing segment renders clean: the invite lines sit over
                # the play instead of the HUD.
                img = render_frame(tau, rich, day_label=label, caption=caption,
                                   clean=(t0 == 10.0))
                if t0 == 10.0:  # closing segment: invite lines on top
                    d = ImageDraw.Draw(img, "RGBA")
                    closing_text(d, i / FPS)
            img.save(os.path.join(OUT, f"f{n:05d}.png"))
            n += 1
    print(f"rendered {n} frames, {TOTAL_S:.1f}s at {FPS} fps -> {OUT}")


if __name__ == "__main__":
    main()
