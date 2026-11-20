"""E-ink renderer: a full-body floating Mantis Tamagotchi for the Pi 2.13".

Draws a small gas-masked psychic figure — gas-masked head, leather coat with tattered
tails, arms posed by mood, bare dangling feet, and a psychic aura — in strict
1-bit black/white at 250x122, then composes it with an expanded stat panel
(PSYCHE / XP / DARKNESS bars, souls, infamy, kills / kidnaps / possessions).

The figure's eyes, pose, aura and floating effects all change with the mood, so
each of the 70 moods reads differently on the panel.

Auto-detects Waveshare 2.13" (epd2in13_V2/V3/V4) or Pimoroni Inky; otherwise
writes scaled PNG previews so you can develop without hardware.
"""

from __future__ import annotations

import math
import os
import threading
import time
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 250, 122
BLACK, WHITE = 0, 255


def _font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


F_BIG, F_MED, F_SM = _font(15), _font(12), _font(9)


def _tw(d, s, f):
    try:
        b = d.textbbox((0, 0), s, font=f)
        return b[2] - b[0]
    except Exception:
        return len(s) * 6


# --------------------------------------------------------------------------- #
# Eyes on the mask lenses
# --------------------------------------------------------------------------- #
def _lens(d, lx, ly, r, eyes):
    d.ellipse([lx - r - 1, ly - r - 1, lx + r + 1, ly + r + 1], fill=BLACK)
    d.ellipse([lx - r, ly - r, lx + r, ly + r], fill=WHITE, outline=BLACK)
    if eyes == "closed":
        d.line([(lx - r + 1, ly), (lx + r - 1, ly)], fill=BLACK, width=2); return
    if eyes == "half":
        d.rectangle([lx - r, ly - r, lx + r, ly - 1], fill=BLACK); return
    if eyes == "cross":
        d.line([(lx - r + 2, ly - r + 2), (lx + r - 2, ly + r - 2)], fill=BLACK, width=2)
        d.line([(lx - r + 2, ly + r - 2), (lx + r - 2, ly - r + 2)], fill=BLACK, width=2); return
    if eyes == "star":
        for a in (0, 45, 90, 135):
            dx, dy = int(r * math.cos(math.radians(a))), int(r * math.sin(math.radians(a)))
            d.line([(lx - dx, ly - dy), (lx + dx, ly + dy)], fill=BLACK, width=1)
        return
    if eyes == "cracked":
        d.ellipse([lx - r, ly - r, lx + r, ly + r], outline=BLACK, width=2)
        d.line([(lx - r, ly - 1), (lx, ly + 2), (lx + r, ly - 2)], fill=BLACK)
        d.line([(lx, ly - r), (lx, ly + r)], fill=BLACK); return
    if eyes == "spiral":
        pr = r
        for a in range(0, 540, 45):
            pr2 = r * (1 - a / 600)
            x = lx + int(pr2 * math.cos(math.radians(a)))
            y = ly + int(pr2 * math.sin(math.radians(a)))
            d.point((x, y), fill=BLACK); d.point((x + 1, y), fill=BLACK)
        return
    if eyes == "tear":
        d.ellipse([lx - 2, ly - 2, lx + 2, ly + 2], fill=BLACK)
        d.line([(lx, ly + 2), (lx, ly + r + 3)], fill=BLACK, width=1); return
    if eyes == "slit":
        d.ellipse([lx - r, ly - 2, lx + r, ly + 2], fill=BLACK); return
    if eyes == "glow":
        d.ellipse([lx - r + 2, ly - r + 2, lx + r - 2, ly + r - 2], fill=BLACK)
        d.ellipse([lx - 1, ly - 1, lx + 1, ly + 1], fill=WHITE); return
    # normal / narrow / wide pupils
    pr = {"narrow": 1, "wide": max(3, r // 2 + 1)}.get(eyes, max(2, r // 2))
    d.ellipse([lx - pr, ly - pr, lx + pr, ly + pr], fill=BLACK)
    d.point((lx - 1, ly - 1), fill=WHITE)


# --------------------------------------------------------------------------- #
# Sprite asset override — use the user's own PNG/BMP art if present
# --------------------------------------------------------------------------- #
def sprite_dir() -> str:
    env = os.environ.get("MANTIS_HOME") or os.environ.get("PSYCHOMANTIS_HOME")
    base = os.path.expanduser(env) if env else os.path.join(os.path.expanduser("~"), ".mantis")
    return os.path.join(base, "sprites")


_SPRITE_CACHE: Dict[str, Any] = {}


def _bundled_sprite_dir() -> str:
    return os.path.join(os.path.dirname(__file__), "assets", "sprites")


def load_sprite(key: str):
    """Load a sprite by key as 1-bit, cached by mtime.

    Looks in the user's <home>/sprites first (their overrides win), then the
    bundled art that ships with MANTIS.
    """
    if not key:
        return None
    for d in (sprite_dir(), _bundled_sprite_dir()):
        for ext in (".png", ".bmp", ".gif"):
            p = os.path.join(d, key + ext)
            if not os.path.exists(p):
                continue
            try:
                mt = os.path.getmtime(p)
            except OSError:
                mt = 0
            cached = _SPRITE_CACHE.get(p)
            if cached and cached[0] == mt:
                return cached[1]
            try:
                im = Image.open(p).convert("1")
            except Exception:
                im = None
            _SPRITE_CACHE[p] = (mt, im)
            return im
    return None


def place_figure(img, box, sprite, keys=None):
    """Paste a user sprite (first matching key) into box, else draw procedurally."""
    if keys:
        if isinstance(keys, str):
            keys = [keys]
        for k in keys:
            ov = load_sprite(k)
            if ov is not None:
                x, y, w, h = box
                ow, oh = ov.size
                scale = min(w / ow, h / oh)
                s = ov.resize((max(1, int(ow * scale)), max(1, int(oh * scale))),
                              Image.NEAREST)
                px = x + (w - s.width) // 2
                py = y + (h - s.height) // 2
                mask = s.point(lambda v: 255 if v < 128 else 0).convert("L")
                img.paste(0, (px, py), mask)      # black pixels of the sprite
                return
    draw_figure(img, box, sprite)


def _fig_keys(snap):
    """Sprite keys to try for the status figure: mood first, then current stage."""
    keys = []
    m = snap.get("mood")
    if m:
        keys.append("mood_" + m)
    st = (snap.get("stage") or {}).get("key")
    if st:
        keys.append("stage_" + st)
    return keys


# --------------------------------------------------------------------------- #
# Full figure
# --------------------------------------------------------------------------- #
def draw_figure(img, box, sprite):
    x, y, w, h = box
    d = ImageDraw.Draw(img)
    eyes = sprite.get("eyes", "normal")
    aura = sprite.get("aura", "none")
    pose = sprite.get("pose", "float")
    fx = sprite.get("fx", "none")

    cx = x + w // 2
    head_r = max(9, int(w * 0.26))
    head_cy = y + head_r + 10
    sh_y = head_cy + head_r                       # shoulder line
    hip_y = sh_y + int(h * 0.26)
    sw = int(w * 0.26)                            # shoulder half width

    if pose == "curl":
        _draw_curled(d, cx, (y + y + h) // 2, int(w * 0.42), eyes, aura, fx)
        _aura(d, cx, (y + y + h) // 2, w, h, aura)
        _fx(d, cx, head_cy, head_r, w, h, fx)
        return

    # aura behind the body
    _aura(d, cx, head_cy, w, h, aura)

    # --- coat tails (tattered) below the hips --------------------------- #
    tail_bottom = y + h - 2
    tat = []
    steps = 6
    for i in range(steps + 1):
        tx = cx - sw - 4 + int((2 * (sw + 4)) * i / steps)
        ty = tail_bottom - (6 if i % 2 else 0)
        tat.append((tx, ty))
    d.polygon([(cx - sw, hip_y), (cx + sw, hip_y)] + list(reversed(tat)), fill=BLACK)

    # --- legs (pose-dependent) ------------------------------------------ #
    leg_len = int(h * 0.22)
    foot = hip_y + leg_len
    if pose == "sit":                       # cross-legged
        d.polygon([(cx - sw, hip_y), (cx + sw, hip_y),
                   (cx + sw + 4, foot), (cx - sw - 4, foot)], fill=BLACK)
        d.line([(cx - sw, foot), (cx + sw, foot - 4)], fill=WHITE)
    elif pose == "kneel":                    # one knee down
        d.line([(cx - int(sw * 0.4), hip_y), (cx - int(sw * 0.4), foot)], fill=BLACK, width=4)
        d.line([(cx + int(sw * 0.4), hip_y), (cx + sw, hip_y + leg_len // 2),
                (cx + sw, foot)], fill=BLACK, width=4)
        d.ellipse([cx - int(sw * 0.4) - 4, foot - 2, cx - int(sw * 0.4) + 4, foot + 2], fill=BLACK)
    elif pose == "run":                      # mid-stride
        d.line([(cx, hip_y), (cx - sw - 4, foot)], fill=BLACK, width=4)
        d.line([(cx, hip_y), (cx + sw + 2, hip_y + leg_len - 4)], fill=BLACK, width=4)
        for fx0 in (cx - sw - 4, cx + sw + 2):
            d.ellipse([fx0 - 3, foot - 2, fx0 + 3, foot + 2], fill=BLACK)
    elif pose == "ride":                     # knees bent forward
        d.line([(cx - int(sw * 0.4), hip_y), (cx - int(sw * 0.4) + 6, hip_y + leg_len)], fill=BLACK, width=4)
        d.line([(cx + int(sw * 0.4), hip_y), (cx + int(sw * 0.4) + 8, hip_y + leg_len)], fill=BLACK, width=4)
    else:                                    # dangling, floating
        for sgn in (-1, 1):
            lx0 = cx + sgn * int(sw * 0.4)
            d.line([(lx0, hip_y), (lx0, foot)], fill=BLACK, width=4)
            d.ellipse([lx0 - 3, foot - 2, lx0 + 3, foot + 2], fill=BLACK)  # bare foot

    # --- torso (leather) ------------------------------------------------ #
    d.polygon([(cx - sw, sh_y), (cx + sw, sh_y),
               (cx + int(sw * 0.7), hip_y), (cx - int(sw * 0.7), hip_y)], fill=BLACK)
    # strap highlights
    d.line([(cx - sw + 2, sh_y + 6), (cx + sw - 2, sh_y + 6)], fill=WHITE)
    d.line([(cx - sw + 4, sh_y + 6), (cx + int(sw * 0.7) - 2, hip_y - 3)], fill=WHITE)
    d.line([(cx + sw - 4, sh_y + 6), (cx - int(sw * 0.7) + 2, hip_y - 3)], fill=WHITE)

    # --- arms (pose) ---------------------------------------------------- #
    hands = _arms(d, cx, sh_y, sw, head_cy, head_r, hip_y, w, h, pose)

    # --- head / gas mask ------------------------------------------------ #
    _head(d, cx, head_cy, head_r, eyes)

    # --- floating effects ----------------------------------------------- #
    _fx(d, cx, head_cy, head_r, w, h, fx, hands)


def _head(d, cx, cy, r, eyes):
    # spiky hair
    for i in range(-2, 3):
        hx = cx + i * (r // 2)
        d.polygon([(hx - 3, cy - r + 2), (hx + 3, cy - r + 2), (hx, cy - r - 7)], fill=BLACK)
    # hood/head
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=BLACK)
    d.polygon([(cx - r + 2, cy + r // 2), (cx + r + 2, cy + r // 2),
               (cx + r // 2, cy + r + 5), (cx - r // 2, cy + r + 5)], fill=BLACK)
    # lenses
    lr = max(3, int(r * 0.42))
    ly = cy - int(r * 0.15)
    _lens(d, cx - int(r * 0.42), ly, lr, eyes)
    _lens(d, cx + int(r * 0.42), ly, lr, eyes)
    # breathing filter
    fw = max(4, int(r * 0.5))
    fy = cy + int(r * 0.55)
    d.rounded_rectangle([cx - fw // 2, fy, cx + fw // 2, fy + int(r * 0.5)],
                        radius=2, fill=WHITE, outline=BLACK)


def _arms(d, cx, sh_y, sw, head_cy, head_r, hip_y, w, h, pose):
    L = (cx - sw, sh_y + 3)
    R = (cx + sw, sh_y + 3)
    far = int(w * 0.46)
    if pose == "arms_raised":
        hl = (cx - sw - 6, head_cy - head_r - 6); hr = (cx + sw + 6, head_cy - head_r - 6)
    elif pose in ("arms_out", "crucifix"):
        ext = far if pose == "crucifix" else int(w * 0.40)
        hl = (cx - ext, sh_y + (0 if pose == "crucifix" else 4))
        hr = (cx + ext, sh_y + (0 if pose == "crucifix" else 4))
    elif pose == "reach":
        hl = (cx - 12, sh_y + 22); hr = (cx + 12, sh_y + 24)
    elif pose == "slump":
        hl = (cx - sw - 2, hip_y + 4); hr = (cx + sw + 2, hip_y + 4)
    elif pose == "point":
        hl = (cx - sw - 2, hip_y); hr = (cx + far, sh_y + 2)
    elif pose == "hover":
        hl = (cx - sw - 2, hip_y); hr = (cx + sw + 8, sh_y - 8)
    elif pose == "listen":                  # one hand cupped to ear
        hl = (cx - sw - 6, sh_y + 16); hr = (cx + head_r + 2, head_cy)
    elif pose == "goggles":                 # both hands up to the visor
        hl = (cx - head_r, head_cy - 2); hr = (cx + head_r, head_cy - 2)
    elif pose == "carry":                   # both hands forward holding something
        hl = (cx - 10, sh_y + 20); hr = (cx + 14, sh_y + 20)
    elif pose == "type":                    # hands low, at a keyboard
        hl = (cx - sw, hip_y + 2); hr = (cx + sw, hip_y + 2)
    elif pose == "ride":                    # hands forward on handlebars
        hl = (cx + sw, sh_y + 10); hr = (cx + sw + 10, sh_y + 8)
    elif pose == "run":                     # pumping arms
        hl = (cx - sw - 6, sh_y - 4); hr = (cx + sw + 4, sh_y + 14)
    else:  # float
        hl = (cx - sw - 8, sh_y + 20); hr = (cx + sw + 8, sh_y + 20)
    for (sx, sy), (hx, hy) in ((L, hl), (R, hr)):
        ex = (sx + hx) // 2 + (2 if hx > sx else -2)
        ey = (sy + hy) // 2
        d.line([(sx, sy), (ex, ey), (hx, hy)], fill=BLACK, width=4)
        d.ellipse([hx - 3, hy - 3, hx + 3, hy + 3], fill=BLACK)      # hand
        # spread fingers for reaching/casting
        if pose in ("reach", "arms_out", "arms_raised", "crucifix"):
            for fa in (-35, -12, 12, 35):
                fxp = hx + int(6 * math.cos(math.radians(90 + fa)))
                fyp = hy - int(6 * math.sin(math.radians(90 + fa)))
                d.line([(hx, hy), (fxp, fyp)], fill=BLACK, width=1)
    return (hl, hr)


def _draw_curled(d, cx, cy, r, eyes, aura, fx):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=BLACK)              # curled body
    hr = max(6, r // 2)
    hx, hy = cx, cy - r + hr // 2
    d.ellipse([hx - hr, hy - hr, hx + hr, hy + hr], fill=BLACK)
    lr = max(2, hr // 2)
    _lens(d, hx - hr // 2, hy, lr, eyes)
    _lens(d, hx + hr // 2, hy, lr, eyes)
    d.arc([cx - r, cy - r, cx + r, cy + r], 20, 160, fill=WHITE, width=1)


# --------------------------------------------------------------------------- #
# Aura + floating effects
# --------------------------------------------------------------------------- #
def _aura(d, cx, cy, w, h, aura):
    if aura == "none":
        return
    R = int(w * 0.52)
    if aura == "waves":
        for rr in (R, R + 7):
            d.arc([cx - rr, cy - rr, cx + rr, cy + rr], 300, 60, fill=BLACK)
            d.arc([cx - rr, cy - rr, cx + rr, cy + rr], 120, 240, fill=BLACK)
    elif aura == "lightning":
        for a in (25, 80, 155, 205, 285, 335):
            x0 = cx + int(R * 0.6 * math.cos(math.radians(a)))
            y0 = cy + int(R * 0.6 * math.sin(math.radians(a)))
            x1 = cx + int(R * math.cos(math.radians(a)))
            y1 = cy + int(R * math.sin(math.radians(a)))
            xm = (x0 + x1) // 2 + (4 if a % 2 else -4)
            d.line([(x0, y0), (xm, (y0 + y1) // 2), (x1, y1)], fill=BLACK)
    elif aura == "flame":
        for a in range(0, 360, 40):
            fx0 = cx + int(R * 0.9 * math.cos(math.radians(a)))
            fy0 = cy + int(R * 0.9 * math.sin(math.radians(a)))
            d.polygon([(fx0 - 3, fy0 + 4), (fx0 + 3, fy0 + 4), (fx0, fy0 - 5)], fill=BLACK)
    elif aura == "smoke":
        for i in range(3):
            sx = cx - 10 + i * 10
            d.arc([sx - 4, cy - h // 2 - 6, sx + 4, cy - h // 2 + 6], 0, 360, fill=BLACK)
    elif aura == "void":
        for a in range(0, 360, 30):
            x1 = cx + int(R * math.cos(math.radians(a)))
            y1 = cy + int(R * math.sin(math.radians(a)))
            x0 = cx + int(R * 0.7 * math.cos(math.radians(a)))
            y0 = cy + int(R * 0.7 * math.sin(math.radians(a)))
            d.line([(x0, y0), (x1, y1)], fill=BLACK, width=2)
    elif aura == "halo":
        d.ellipse([cx - 12, cy - 22, cx + 12, cy - 14], outline=BLACK, width=2)
    elif aura == "static":
        import random as _r
        for _ in range(26):
            px = cx + _r.randint(-R, R); py = cy + _r.randint(-R // 2, R)
            d.point((px, py), fill=BLACK)


def _fx(d, cx, head_cy, head_r, w, h, fx, hands=None):
    if fx == "none":
        return
    if fx == "binary":
        import random as _r
        for _ in range(6):
            bx = cx + _r.randint(-int(w * 0.45), int(w * 0.45))
            by = head_cy - head_r - _r.randint(2, 14)
            d.text((bx, by), _r.choice("01"), font=F_SM, fill=BLACK)
    elif fx == "grid":
        gx0 = cx + int(w * 0.28)
        for r in range(3):
            for c in range(3):
                d.rectangle([gx0 + c * 6, head_cy + r * 6, gx0 + c * 6 + 2,
                             head_cy + r * 6 + 2], fill=BLACK)
    elif fx == "zzz":
        for i, s in enumerate("zzz"):
            d.text((cx + head_r + 2 + i * 5, head_cy - head_r - i * 5), s, font=F_SM, fill=BLACK)
    elif fx == "tarot":
        tx, ty = cx + int(w * 0.32), head_cy - head_r - 4
        d.rectangle([tx, ty, tx + 9, ty + 13], outline=BLACK)
        d.line([(tx + 2, ty + 4), (tx + 7, ty + 4)], fill=BLACK)
        d.line([(tx + 4, ty + 2), (tx + 4, ty + 10)], fill=BLACK)
    elif fx == "skull":
        sx, sy = cx + int(w * 0.34), head_cy
        d.ellipse([sx - 4, sy - 4, sx + 4, sy + 4], fill=WHITE, outline=BLACK)
        d.point((sx - 2, sy - 1), fill=BLACK); d.point((sx + 2, sy - 1), fill=BLACK)
        d.line([(sx - 2, sy + 3), (sx + 2, sy + 3)], fill=BLACK)
    elif fx == "chains":
        hx = hands[0][0] if hands else cx - int(w * 0.3)
        hy = (hands[0][1] if hands else head_cy) + 4
        for i in range(3):
            d.ellipse([hx - 2, hy + i * 6, hx + 2, hy + i * 6 + 5], outline=BLACK)
    elif fx == "ghost":
        gx, gy = cx + int(w * 0.34), head_cy + 6
        d.pieslice([gx - 5, gy - 6, gx + 5, gy + 4], 180, 360, fill=WHITE, outline=BLACK)
        d.rectangle([gx - 5, gy - 1, gx + 5, gy + 4], fill=WHITE, outline=None)
        d.line([(gx - 5, gy + 4), (gx - 2, gy + 1), (gx + 1, gy + 4), (gx + 5, gy + 1)], fill=BLACK)
        d.point((gx - 2, gy - 1), fill=BLACK); d.point((gx + 2, gy - 1), fill=BLACK)
    elif fx == "blood":
        hx = hands[1][0] if hands else cx + int(w * 0.3)
        hy = (hands[1][1] if hands else head_cy) + 3
        for i in range(3):
            d.line([(hx + i * 3 - 3, hy), (hx + i * 3 - 3, hy + 6 + i)], fill=BLACK)
    elif fx == "crown":
        cwd = head_r + 2
        base = head_cy - head_r - 8
        pts = [(cx - cwd, base), (cx - cwd // 2, base - 6), (cx, base),
               (cx + cwd // 2, base - 6), (cx + cwd, base)]
        d.line(pts, fill=BLACK, width=2)
    elif fx == "question":
        d.text((cx + head_r + 2, head_cy - head_r - 6), "?", font=F_MED, fill=BLACK)


# --------------------------------------------------------------------------- #
# Full 250x122 screen
# --------------------------------------------------------------------------- #
def _bar(d, x, y, w, h, pct, label):
    if label:
        d.text((x, y - 9), label, font=F_SM, fill=BLACK)
    d.rectangle([x, y, x + w, y + h], outline=BLACK)
    fw = int((w - 2) * max(0, min(100, pct)) / 100)
    if fw > 0:
        d.rectangle([x + 1, y + 1, x + 1 + fw, y + h - 1], fill=BLACK)


def _battery_icon(d, x, y, pct, charging=False):
    w, h = 16, 8
    d.rectangle([x, y, x + w, y + h], outline=BLACK)
    d.rectangle([x + w, y + 2, x + w + 2, y + h - 2], fill=BLACK)      # nub
    fillw = int((w - 2) * max(0, min(100, pct)) / 100)
    if fillw > 0:
        d.rectangle([x + 1, y + 1, x + 1 + fillw, y + h - 1], fill=BLACK)
    if charging:
        d.line([(x + w // 2 + 1, y), (x + w // 2 - 2, y + h // 2),
                (x + w // 2 + 2, y + h // 2), (x + w // 2 - 1, y + h)], fill=WHITE)


def render_screen(snap, size=(WIDTH, HEIGHT), bob=0, battery=None):
    W, H = size
    img = Image.new("1", (W, H), WHITE)
    d = ImageDraw.Draw(img)

    fw = int(W * 0.37)
    place_figure(img, (0, bob, fw, H - 14), snap.get("sprite", {}), keys=_fig_keys(snap))
    d.line([(fw + 2, 2), (fw + 2, H - 16)], fill=BLACK)

    rx = fw + 8
    batt_w = 22 if battery is not None else 0
    name = snap.get("name", "Mantis")
    while name and _tw(d, name, F_BIG) > W - rx - 2 - batt_w:
        name = name[:-1]
    d.text((rx, 1), name, font=F_BIG, fill=BLACK)
    if battery is not None:
        _battery_icon(d, W - 20, 3, battery.get("percent", 0), battery.get("charging"))
    lv = snap.get("level", 1)
    d.text((rx, 16), f"LV {lv}/{snap.get('level_cap', 100)} {snap.get('rank','')[:12]}",
           font=F_SM, fill=BLACK)
    stage = snap.get("stage") or {}
    if stage.get("label"):
        d.text((rx, 26), "> " + stage["label"][:18], font=F_SM, fill=BLACK)

    bw = W - rx - 4
    _bar(d, rx, 45, bw, 5, snap.get("psyche_pct", 0), "PSY")
    _bar(d, rx, 60, bw, 5, snap.get("xp_pct", 0), "XP")
    _bar(d, rx, 75, bw, 5, snap.get("darkness", 0), "DARK")

    st = snap.get("stats", {})
    d.text((rx, 84), f"{snap.get('souls',0)} souls  infamy {snap.get('infamy',0)}",
           font=F_SM, fill=BLACK)
    d.text((rx, 95), f"K{st.get('kills',0)} N{st.get('kidnappings',0)} "
                     f"P{st.get('possessions',0)} nets{st.get('networks_sensed',0)}",
           font=F_SM, fill=BLACK)

    # bottom phrase bar (inverted)
    d.rectangle([0, H - 13, W, H], fill=BLACK)
    phrase = _truncate(d, snap.get("phrase", "..."), F_SM, W - 6)
    d.text((3, H - 12), phrase, font=F_SM, fill=WHITE)
    return img


def _truncate(d, s, f, maxw):
    if _tw(d, s, f) <= maxw:
        return s
    while s and _tw(d, s + "…", f) > maxw:
        s = s[:-1]
    return s + "…"


def render_sleep(snap, battery=None, size=(WIDTH, HEIGHT)):
    """Low-power hibernation screen (drawn once, then the panel deep-sleeps)."""
    W, H = size
    img = Image.new("1", (W, H), WHITE)
    d = ImageDraw.Draw(img)
    # curled sleeping figure, centered-left
    draw_figure(img, (0, 0, int(W * 0.40), H - 14),
                {"eyes": "closed", "aura": "none", "pose": "curl", "fx": "zzz"})
    rx = int(W * 0.40) + 10
    d.text((rx, 10), snap.get("name", "Mantis")[:14], font=F_BIG, fill=BLACK)
    d.text((rx, 30), "HIBERNATING", font=F_MED, fill=BLACK)
    d.text((rx, 46), "low power - conserving", font=F_SM, fill=BLACK)
    if battery is not None:
        _battery_icon(d, rx, 64, battery.get("percent", 0), battery.get("charging"))
        d.text((rx + 24, 63), f"{int(battery.get('percent', 0))}%", font=F_SM, fill=BLACK)
    d.rectangle([0, H - 13, W, H], fill=BLACK)
    d.text((3, H - 12), "I sleep until the power returns...", font=F_SM, fill=WHITE)
    return img


# --------------------------------------------------------------------------- #
# Stage props — themed cyber-activity scenes (1-bit icons) for stage cards
# --------------------------------------------------------------------------- #
def _dither(d, box, step=2):
    x0, y0, x1, y1 = box
    for yy in range(int(y0), int(y1)):
        for xx in range(int(x0) + (yy % step), int(x1), step):
            d.point((xx, yy), fill=BLACK)


def _waves(d, cx, cy, n=3, r0=6, step=6, span=(300, 60)):
    for i in range(n):
        rr = r0 + i * step
        d.arc([cx - rr, cy - rr, cx + rr, cy + rr], span[0], span[1], fill=BLACK)


def _server(d, x, y, w=16, h=22):
    d.rectangle([x, y, x + w, y + h], outline=BLACK, width=1)
    for i in range(3):
        yy = y + 4 + i * (h - 6) // 3
        d.line([(x + 3, yy), (x + w - 3, yy)], fill=BLACK)
        d.point((x + w - 4, yy), fill=BLACK)


def _database(d, cx, y, w=18, h=22):
    d.ellipse([cx - w // 2, y, cx + w // 2, y + 6], outline=BLACK)
    d.line([(cx - w // 2, y + 3), (cx - w // 2, y + h)], fill=BLACK)
    d.line([(cx + w // 2, y + 3), (cx + w // 2, y + h)], fill=BLACK)
    d.arc([cx - w // 2, y + h - 6, cx + w // 2, y + h], 0, 180, fill=BLACK)
    d.arc([cx - w // 2, y + h // 2 - 3, cx + w // 2, y + h // 2 + 3], 0, 180, fill=BLACK)


def _key(d, x, y, s=6):
    d.ellipse([x, y, x + s, y + s], outline=BLACK)
    d.line([(x + s, y + s // 2), (x + s + 8, y + s // 2)], fill=BLACK)
    d.line([(x + s + 6, y + s // 2), (x + s + 6, y + s // 2 + 3)], fill=BLACK)


def _lock(d, cx, y, w=14, h=12, broken=False):
    d.rectangle([cx - w // 2, y + 5, cx + w // 2, y + 5 + h], outline=BLACK, width=1)
    arc = 220 if broken else 180
    d.arc([cx - w // 2 + 2, y - 2, cx + w // 2 - 2, y + 10], arc, 360, fill=BLACK)
    d.point((cx, y + 10), fill=BLACK)
    if broken:
        d.line([(cx - 3, y + 7), (cx + 2, y + 12), (cx - 1, y + 16)], fill=WHITE)


def _window(d, x, y, w=26, h=18, term=False):
    d.rectangle([x, y, x + w, y + h], outline=BLACK, width=1)
    d.line([(x, y + 4), (x + w, y + 4)], fill=BLACK)
    d.ellipse([x + 2, y + 1, x + 3, y + 2], fill=BLACK)
    if term:
        d.text((x + 3, y + 6), ">_", font=F_SM, fill=BLACK)


def _computer(d, x, y, w=16, h=12):
    d.rectangle([x, y, x + w, y + h], outline=BLACK)
    d.line([(x + 3, y + h), (x + w - 3, y + h)], fill=BLACK)
    d.line([(x + w // 2, y + h), (x + w // 2, y + h + 2)], fill=BLACK)


def _bolt(d, x, y, h=10):
    d.line([(x, y), (x - 3, y + h // 2), (x + 1, y + h // 2), (x - 2, y + h)], fill=BLACK)


def _draw_prop(d, box, name):
    """Draw a themed scene for a stage inside box=(x0,y0,x1,y1)."""
    x0, y0, x1, y1 = box
    w = x1 - x0
    h = y1 - y0
    cx = (x0 + x1) // 2
    cy = (y0 + y1) // 2
    import random as _r

    if name in ("none", None):
        return
    if name == "netgraph":
        pts = [(x0 + 6, y1 - 6), (cx, cy), (x1 - 8, y1 - 10),
               (x0 + 12, cy - 6), (x1 - 6, cy + 8)]
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                if (i + j) % 2 == 0:
                    d.line([pts[i], pts[j]], fill=BLACK)
        for px, py in pts:
            d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=BLACK)
    elif name == "radar":
        for rr in (6, 13, 20):
            d.ellipse([cx - rr, cy - rr, cx + rr, cy + rr], outline=BLACK)
        d.line([(cx, cy), (cx + 18, cy - 12)], fill=BLACK)
        d.ellipse([cx + 8, cy + 4, cx + 12, cy + 8], fill=BLACK)   # blip
    elif name == "handshake":
        _lock(d, cx, y0 + 2)
        d.line([(cx - 14, cy + 8), (cx, cy + 4), (cx + 14, cy + 8)], fill=BLACK, width=3)
        _key(d, cx - 6, y1 - 10)
    elif name == "nowifi":
        _waves(d, cx, cy + 6, 3, 6, 6, (210, 330))
        d.line([(cx - 12, cy - 10), (cx + 12, cy + 12)], fill=BLACK, width=2)
    elif name == "binarycols":
        for c in range(4):
            for r2 in range(4):
                d.text((x0 + 4 + c * 10, y0 + 2 + r2 * 10), _r.choice("01"),
                       font=F_SM, fill=BLACK)
    elif name == "mask":
        d.ellipse([cx - 9, cy - 7, cx + 9, cy + 9], outline=BLACK, width=2)
        d.ellipse([cx - 5, cy - 2, cx - 1, cy + 2], fill=BLACK)
        d.ellipse([cx + 1, cy - 2, cx + 5, cy + 2], fill=BLACK)
    elif name == "jam":
        for i in range(10):
            xx = x0 + 4 + i * (w - 8) // 10
            d.line([(xx, cy - _r.randint(2, 12)), (xx, cy + _r.randint(2, 12))], fill=BLACK)
        d.text((cx - 10, y0), "JAM", font=F_SM, fill=BLACK)
    elif name == "lockkeys":
        _lock(d, cx, y0 + 2)
        for i in range(3):
            _key(d, x0 + 2 + i * 6, y1 - 12 - i * 2)
    elif name == "lockcrack":
        _lock(d, cx, cy - 6, broken=True)
        _key(d, cx + 6, y1 - 10)
    elif name == "crowbar":
        _lock(d, cx + 6, cy, broken=True)
        d.line([(x0 + 2, y1 - 2), (cx, cy - 6)], fill=BLACK, width=3)
        d.line([(x0 + 2, y1 - 2), (x0 + 6, y1 - 6)], fill=BLACK, width=3)
    elif name == "wallcheck":
        for r2 in range(3):
            off = 6 if r2 % 2 else 0
            for c in range(3):
                d.rectangle([x0 + off + c * 12, cy - 12 + r2 * 8,
                             x0 + off + c * 12 + 11, cy - 12 + r2 * 8 + 7], outline=BLACK)
        d.line([(cx - 2, y1 - 8), (cx + 1, y1 - 4), (cx + 8, y1 - 14)], fill=BLACK, width=2)
    elif name == "stairs":
        for i in range(4):
            yy = y1 - 4 - i * 6
            d.rectangle([x0 + 4 + i * 8, yy - 6, x0 + 4 + i * 8 + 10, yy], outline=BLACK)
        d.line([(x1 - 6, y0 + 6), (x1 - 6, y0 + 2)], fill=BLACK)
        d.line([(x1 - 9, y0 + 5), (x1 - 6, y0 + 1), (x1 - 3, y0 + 5)], fill=BLACK)
    elif name == "flag":
        d.line([(cx, y0 + 2), (cx, y1 - 4)], fill=BLACK, width=2)
        d.polygon([(cx, y0 + 2), (cx + 14, y0 + 6), (cx, y0 + 12)], fill=BLACK)
        d.arc([cx - 8, y1 - 10, cx + 8, y1 + 2], 180, 360, fill=BLACK)   # mound
    elif name == "briefcase":
        d.rectangle([cx - 12, cy - 6, cx + 12, cy + 12], outline=BLACK)
        d.rectangle([cx - 4, cy - 10, cx + 4, cy - 6], outline=BLACK)
        for a in (0, 120, 240):   # radiation trefoil
            dx = int(7 * math.cos(math.radians(a - 90)))
            dy = int(7 * math.sin(math.radians(a - 90)))
            d.line([(cx, cy + 3), (cx + dx, cy + 3 + dy)], fill=BLACK, width=2)
    elif name == "docs":
        for i in range(3):
            dx, dy = x0 + 6 + i * 4, y0 + 4 + i * 5
            d.rectangle([dx, dy, dx + 16, dy + 20], fill=WHITE, outline=BLACK)
            for ln in range(3):
                d.line([(dx + 3, dy + 5 + ln * 4), (dx + 13, dy + 5 + ln * 4)], fill=BLACK)
    elif name == "bag":
        d.pieslice([cx - 10, cy - 6, cx + 10, cy + 14], 0, 360, fill=BLACK)
        d.line([(cx - 4, cy - 6), (cx, cy - 12), (cx + 4, cy - 6)], fill=BLACK)
        for i in range(3):
            d.line([(x0, cy + i * 5), (x0 + 8, cy + i * 5)], fill=BLACK)   # motion
    elif name == "sponge":
        d.rounded_rectangle([cx - 10, cy - 6, cx + 10, cy + 6], radius=3, fill=BLACK)
        for i in range(4):
            d.line([(cx - 8 + i * 5, cy + 7), (cx - 8 + i * 5, cy + 7 + 6)], fill=BLACK)
    elif name == "speaker":
        d.rectangle([cx - 10, cy - 5, cx - 4, cy + 5], fill=BLACK)
        d.polygon([(cx - 4, cy - 5), (cx + 2, cy - 10), (cx + 2, cy + 10), (cx - 4, cy + 5)], fill=BLACK)
        _waves(d, cx + 2, cy, 3, 5, 5, (300, 60))
    elif name == "circuit":
        d.rectangle([cx - 9, cy - 9, cx + 9, cy + 9], fill=BLACK)
        for i in range(4):
            d.line([(cx - 9, cy - 6 + i * 4), (cx - 14, cy - 6 + i * 4)], fill=BLACK)
            d.line([(cx + 9, cy - 6 + i * 4), (cx + 14, cy - 6 + i * 4)], fill=BLACK)
        d.rectangle([cx - 4, cy - 4, cx + 4, cy + 4], outline=WHITE)
    elif name == "scooter":
        d.ellipse([x0 + 2, y1 - 10, x0 + 12, y1], outline=BLACK, width=2)
        d.ellipse([x1 - 12, y1 - 10, x1 - 2, y1], outline=BLACK, width=2)
        d.line([(x0 + 7, y1 - 5), (cx, cy), (x1 - 7, y1 - 5)], fill=BLACK, width=2)
        d.line([(cx, cy), (cx + 4, y0 + 6)], fill=BLACK, width=2)
        _waves(d, x1 - 6, y0 + 8, 2, 4, 4, (300, 60))
    elif name == "lighthouse":
        d.polygon([(cx - 6, y1), (cx + 6, y1), (cx + 4, cy - 6), (cx - 4, cy - 6)], fill=BLACK)
        d.rectangle([cx - 5, cy - 12, cx + 5, cy - 6], outline=BLACK)
        d.polygon([(cx + 5, cy - 10), (x1 - 2, cy - 14), (x1 - 2, cy - 6)], fill=BLACK)  # beam
    elif name == "twin":
        d.rectangle([cx - 16, cy - 10, cx - 4, cy + 10], outline=BLACK)
        d.rectangle([cx + 4, cy - 10, cx + 16, cy + 10], outline=BLACK)
        _dither(d, (cx + 5, cy - 9, cx + 15, cy + 9))
        _lock(d, cx, cy - 6)
    elif name == "mitm":
        d.ellipse([x0 + 2, cy - 4, x0 + 10, cy + 4], outline=BLACK)
        d.ellipse([x1 - 10, cy - 4, x1 - 2, cy + 4], outline=BLACK)
        d.line([(x0 + 10, cy), (x1 - 10, cy)], fill=BLACK)
        d.rectangle([cx - 4, cy - 10, cx + 4, cy - 2], fill=BLACK)
    elif name == "netserver":
        _server(d, x1 - 18, cy - 10)
        for px, py in [(x0 + 4, cy - 8), (x0 + 6, cy + 8), (cx, cy)]:
            d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=BLACK)
            d.line([(px, py), (x1 - 18, cy)], fill=BLACK)
    elif name == "browser":
        _window(d, x0 + 2, y0 + 2)
        _window(d, x0 + 10, cy + 2)
        d.line([(x0 + 28, y0 + 10), (cx + 2, cy + 6)], fill=BLACK, width=1)
    elif name == "binoculars":
        d.ellipse([cx - 12, cy - 6, cx - 2, cy + 6], outline=BLACK, width=2)
        d.ellipse([cx + 2, cy - 6, cx + 12, cy + 6], outline=BLACK, width=2)
        d.line([(cx - 2, cy), (cx + 2, cy)], fill=BLACK)
        d.text((x0 + 2, y1 - 10), "80 443", font=F_SM, fill=BLACK)
    elif name == "checklist":
        d.rectangle([cx - 10, cy - 12, cx + 10, cy + 12], outline=BLACK)
        for i in range(3):
            yy = cy - 7 + i * 7
            if i == 1:
                d.line([(cx - 6, yy), (cx - 3, yy + 3), (cx + 2, yy - 3)], fill=BLACK)
            else:
                d.line([(cx - 6, yy - 2), (cx - 2, yy + 2)], fill=BLACK)
                d.line([(cx - 6, yy + 2), (cx - 2, yy - 2)], fill=BLACK)
            d.line([(cx, yy), (cx + 7, yy)], fill=BLACK)
    elif name == "doorkeys":
        d.rectangle([cx - 2, cy - 14, cx + 12, cy + 14], outline=BLACK)
        d.ellipse([cx + 7, cy - 1, cx + 10, cy + 2], fill=BLACK)   # knob
        for i in range(2):
            _key(d, x0 + 2, cy - 6 + i * 10)
    elif name == "folders":
        d.polygon([(x0 + 2, cy - 8), (x0 + 8, cy - 8), (x0 + 10, cy - 5),
                   (x0 + 20, cy - 5), (x0 + 20, cy + 8), (x0 + 2, cy + 8)], outline=BLACK)
        for i in range(3):
            d.rectangle([cx + 4, cy - 10 + i * 8, cx + 16, cy - 10 + i * 8 + 6], outline=BLACK)
            d.line([(x0 + 20, cy), (cx + 4, cy - 7 + i * 8)], fill=BLACK)
    elif name == "database":
        _database(d, cx, y0 + 4)
        d.text((cx - 14, y1 - 10), "OR 1=1", font=F_SM, fill=BLACK)
    elif name == "databasekeys":
        _database(d, cx - 4, y0 + 4)
        _key(d, x1 - 14, y1 - 12)
        _key(d, x1 - 14, y1 - 22)
    elif name == "formcode":
        for i in range(2):
            d.rectangle([x0 + 2, y0 + 4 + i * 10, x0 + 20, y0 + 4 + i * 10 + 6], outline=BLACK)
        d.text((cx + 2, cy - 4), "</>", font=F_SM, fill=BLACK)
    elif name == "terminal":
        _window(d, x0 + 2, cy - 9, term=True)
        d.line([(x0 + 28, cy), (x1 - 16, cy)], fill=BLACK)
        d.polygon([(x1 - 18, cy - 3), (x1 - 14, cy), (x1 - 18, cy + 3)], fill=BLACK)
        _server(d, x1 - 14, cy - 11, 12, 20)
    elif name == "keyboard":
        d.rectangle([x0 + 2, cy + 2, x1 - 2, cy + 14], outline=BLACK)
        for r2 in range(2):
            for c in range(6):
                d.rectangle([x0 + 5 + c * 6, cy + 5 + r2 * 4, x0 + 5 + c * 6 + 3,
                             cy + 5 + r2 * 4 + 2], fill=BLACK)
        d.ellipse([cx - 5, y0 + 2, cx + 5, y0 + 12], outline=BLACK)   # victim head
    elif name == "rainbow":
        for i in range(5):
            rr = 10 + i * 4
            d.arc([cx - rr, cy - rr + 6, cx + rr, cy + rr + 6], 180, 360, fill=BLACK)
        d.text((x0 + 2, y1 - 10), "HASH", font=F_SM, fill=BLACK)
        _key(d, x1 - 12, y1 - 12)
    elif name == "rfwave":
        d.rectangle([x0 + 2, cy - 5, x0 + 12, cy + 5], outline=BLACK)
        d.text((x0 + 3, cy - 4), "RF", font=F_SM, fill=BLACK)
        pts = [(x0 + 14 + i * 3, cy + (6 if i % 2 else -6)) for i in range(6)]
        d.line(pts, fill=BLACK)
        _waves(d, x1 - 8, cy, 2, 4, 4, (300, 60))
    elif name == "spectrum":
        for i, hgt in enumerate([6, 14, 9, 18, 7, 12]):
            bx = x0 + 3 + i * 6
            d.rectangle([bx, y1 - 8 - hgt, bx + 4, y1 - 8], fill=BLACK)
        d.text((x0 + 2, y1 - 8), "433", font=F_SM, fill=BLACK)
    elif name == "mesh":
        nodes = [(x0 + 6, y0 + 8), (cx, cy - 4), (x1 - 8, y0 + 10),
                 (x0 + 12, y1 - 8), (x1 - 10, y1 - 6)]
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                d.line([nodes[i], nodes[j]], fill=BLACK)
        for nx, ny in nodes:
            d.polygon([(nx, ny - 4), (nx - 3, ny + 3), (nx + 3, ny + 3)], fill=BLACK)  # tower
    elif name == "bluetooth":
        for _ in range(10):
            bx = x0 + _r.randint(2, w - 6); by = y0 + _r.randint(2, h - 8)
            d.line([(bx, by), (bx, by + 5)], fill=BLACK)
            d.line([(bx, by), (bx + 2, by + 1)], fill=BLACK)
        _computer(d, x1 - 16, y1 - 14)
    elif name == "usb":
        d.rectangle([x0 + 2, cy - 4, x0 + 16, cy + 4], outline=BLACK)
        d.rectangle([x0 + 14, cy - 2, x0 + 20, cy + 2], fill=BLACK)
        _window(d, cx + 2, cy - 9, term=True)
    elif name == "circuitbytes":
        _circuit_board = d.rectangle([x0 + 2, cy - 10, x0 + 18, cy + 10], outline=BLACK)
        d.rectangle([x0 + 7, cy - 4, x0 + 13, cy + 4], fill=BLACK)
        d.text((cx, y0 + 2), "BYTE", font=F_SM, fill=BLACK)
        _database(d, x1 - 10, cy - 6, 14, 18)
    elif name == "cabinetkey":
        _server(d, cx - 8, y0 + 4, 18, 28)
        _key(d, cx + 10, cy)
    elif name == "pivot":
        d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=BLACK)
        for px, py in [(x0 + 4, y0 + 4), (x1 - 16, y0 + 4),
                       (x0 + 4, y1 - 14), (x1 - 16, y1 - 14)]:
            _computer(d, px, py)
            d.line([(cx, cy), (px + 8, py + 6)], fill=BLACK)
    elif name == "roottree":
        d.rectangle([cx - 6, y0 + 2, cx + 6, y0 + 10], outline=BLACK)
        for px in (x0 + 6, cx, x1 - 12):
            d.rectangle([px, cy - 2, px + 10, cy + 6], outline=BLACK)
            d.line([(cx, y0 + 10), (px + 5, cy - 2)], fill=BLACK)
        for i in range(5):     # tendril roots
            rx = x0 + 6 + i * (w - 12) // 5
            d.line([(rx, y1 - 10), (rx + _r.choice((-4, 4)), y1 - 2)], fill=BLACK)
    else:
        # unknown prop: a generic data glyph
        d.text((cx - 6, cy - 4), "?", font=F_MED, fill=BLACK)


def render_splash(size=(WIDTH, HEIGHT), name="MANTIS", tagline="I can read your mind..."):
    """Boot splash — big wordmark, the mask, a tagline."""
    W, H = size
    img = Image.new("1", (W, H), WHITE)
    d = ImageDraw.Draw(img)
    # wordmark, letter-spaced and boxed like a logo
    letters = " ".join(name.upper())
    lw = _tw(d, letters, F_BIG)
    lx = (W - lw) // 2
    d.rectangle([lx - 8, 4, lx + lw + 6, 24], outline=BLACK, width=2)
    d.text((lx, 7), letters, font=F_BIG, fill=BLACK)
    # the mask figure, centre
    draw_figure(img, (W // 2 - 42, 22, 84, H - 36),
                {"eyes": "glow", "aura": "waves", "pose": "float", "fx": "none"})
    # tagline bar
    d.rectangle([0, H - 14, W, H], fill=BLACK)
    tw = _tw(d, tagline, F_SM)
    d.text(((W - tw) // 2, H - 13), tagline, font=F_SM, fill=WHITE)
    return img


def render_message(title, sub="", eyes="closed", pose="float",
                   fx="none", aura="none", size=(WIDTH, HEIGHT)):
    """A centred message screen (power-off, hold-to-confirm, etc.)."""
    W, H = size
    img = Image.new("1", (W, H), WHITE)
    d = ImageDraw.Draw(img)
    draw_figure(img, (6, 6, int(W * 0.40), H - 20),
                {"eyes": eyes, "aura": aura, "pose": pose, "fx": fx})
    rx = int(W * 0.44)
    d.text((rx, 24), title[:16], font=F_BIG, fill=BLACK)
    if sub:
        d.text((rx, 44), sub[:26], font=F_SM, fill=BLACK)
    d.rectangle([0, H - 14, W, H], fill=BLACK)
    tag = "MANTIS"
    d.text(((W - _tw(d, tag, F_SM)) // 2, H - 13), tag, font=F_SM, fill=WHITE)
    return img


def render_posture(snap, size=(WIDTH, HEIGHT)):
    """Security posture screen: big grade + per-ward breakdown."""
    W, H = size
    img = Image.new("1", (W, H), WHITE)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 14], fill=BLACK)
    d.text((4, 1), "SECURITY POSTURE", font=F_SM, fill=WHITE)
    p = snap.get("posture", {}) or {}
    grade = p.get("grade", "?")
    score = p.get("score")
    # big grade letter on the left
    d.rectangle([6, 20, 56, 86], outline=BLACK, width=2)
    try:
        big = _font(46)
    except Exception:
        big = F_BIG
    gw = _tw(d, grade, big)
    d.text((6 + (50 - gw) // 2, 28), grade, font=big, fill=BLACK)
    d.text((10, 90), ("—" if score is None else f"{score}/100"), font=F_SM, fill=BLACK)
    # component list on the right
    rx = 66
    for i, c in enumerate(p.get("components", [])[:4]):
        sc = "—" if c.get("score") is None else str(c["score"])
        d.text((rx, 20 + i * 15), f"[{c.get('grade','?')}] {c.get('label','')[:11]}",
               font=F_SM, fill=BLACK)
        vw = _tw(d, sc, F_SM)
        d.text((W - vw - 6, 20 + i * 15), sc, font=F_SM, fill=BLACK)
    d.rectangle([0, H - 13, W, H], fill=BLACK)
    cast = p.get("known", 0)
    d.text((3, H - 12), f"{cast}/{p.get('total',4)} wards cast  (cast more to grade)",
           font=F_SM, fill=WHITE)
    return img


def render_menu(menu, battery=None, size=(WIDTH, HEIGHT)):
    """Draw the on-device settings menu (scrolling list, selected row inverted)."""
    W, H = size
    img = Image.new("1", (W, H), WHITE)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 14], fill=BLACK)
    d.text((4, 1), "SETTINGS", font=F_SM, fill=WHITE)
    if battery is not None:
        _battery_icon(d, W - 20, 2, battery.get("percent", 0), battery.get("charging"))

    rows = menu.rows()
    visible = 8
    top = max(0, min(menu.sel - visible // 2, len(rows) - visible))
    y = 17
    for i in range(top, min(top + visible, len(rows))):
        label, value, selected = rows[i]
        fg = BLACK
        if selected:
            d.rectangle([2, y - 1, W - 2, y + 10], fill=BLACK)
            fg = WHITE
        d.text((6, y), label[:14], font=F_SM, fill=fg)
        vw = _tw(d, value, F_SM)
        d.text((W - vw - 8, y), value, font=F_SM, fill=fg)
        y += 12
    # hint bar
    d.rectangle([0, H - 13, W, H], fill=BLACK)
    d.text((3, H - 12), "med/cast:move  feed/pet:edit  deed:save",
           font=F_SM, fill=WHITE)
    return img


def render_about(snap, version, size=(WIDTH, HEIGHT)):
    """On-device 'about' screen: version + pet identity + lifetime stats."""
    W, H = size
    img = Image.new("1", (W, H), WHITE)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 15], fill=BLACK)
    d.text((4, 1), f"MANTIS  v{version}", font=F_SM, fill=WHITE)
    draw_figure(img, (0, 14, int(W * 0.34), H - 16),
                {"eyes": "glow", "aura": "none", "pose": "float", "fx": "none"})
    rx = int(W * 0.36)
    st = snap.get("stats", {})
    lines = [
        snap.get("name", "Mantis"),
        f"LV {snap.get('level',1)}/{snap.get('level_cap',100)} {snap.get('rank','')[:12]}",
        f"stage: {(snap.get('stage') or {}).get('label','')[:16]}",
        f"academy: {(snap.get('academy') or {}).get('tier','')[:18]}",
        f"nets {st.get('networks_sensed',0)}  souls {snap.get('souls',0)}",
        f"K{st.get('kills',0)} N{st.get('kidnappings',0)} P{st.get('possessions',0)} "
        f"spl {st.get('spells_cast',0)}",
    ]
    for i, ln in enumerate(lines):
        d.text((rx, 18 + i * 11), ln[:26], font=F_SM, fill=BLACK)
    d.rectangle([0, H - 13, W, H], fill=BLACK)
    foot = "FIREFOX // always listening..."
    d.text((3, H - 12), foot[:40], font=F_SM, fill=WHITE)
    return img


def render_stage_card(stage, level, battery=None, size=(WIDTH, HEIGHT)):
    """Full-screen evolution card: figure + themed scene + big label."""
    W, H = size
    img = Image.new("1", (W, H), WHITE)
    d = ImageDraw.Draw(img)
    # LV badge
    d.rectangle([0, 0, 40, 14], fill=BLACK)
    d.text((3, 1), f"LV {level}", font=F_SM, fill=WHITE)
    if battery is not None:
        _battery_icon(d, W - 20, 2, battery.get("percent", 0), battery.get("charging"))
    # figure (left) + prop scene (right)
    sprite = {"eyes": "normal", "aura": stage.get("aura", "none"),
              "pose": stage.get("pose", "float"), "fx": stage.get("fx", "none")}
    place_figure(img, (2, 12, int(W * 0.44), H - 18), sprite,
                 keys=["stage_" + (stage.get("key") or "")])
    _draw_prop(d, (int(W * 0.46), 18, W - 6, H - 20), stage.get("prop", "none"))
    # big label bar
    d.rectangle([0, H - 16, W, H], fill=BLACK)
    label = stage.get("label", "")
    lw = _tw(d, label, F_MED)
    d.text(((W - lw) // 2, H - 15), label, font=F_MED, fill=WHITE)
    return img


# --------------------------------------------------------------------------- #
# Display driver
# --------------------------------------------------------------------------- #
class EInkDisplay:
    def __init__(self, home=None, rotate=0, driver="auto"):
        self.rotate = rotate
        self.mode = "preview"
        self.epd = None
        self.inky = None
        self.preview_dir = os.path.join(
            home or os.path.join(os.path.expanduser("~"), ".mantis"), "eink")
        os.makedirs(self.preview_dir, exist_ok=True)
        self._init_driver(driver)

    def _init_driver(self, driver):
        if driver in ("auto", "waveshare"):
            for mod in ("epd2in13_V4", "epd2in13_V3", "epd2in13_V2", "epd2in13"):
                try:
                    pkg = __import__(f"waveshare_epd.{mod}", fromlist=[mod])
                    self.epd = pkg.EPD(); self.epd.init()
                    try:
                        self.epd.Clear(0xFF)
                    except Exception:
                        pass
                    self.mode = "waveshare"; return
                except Exception:
                    continue
        if driver in ("auto", "inky"):
            try:
                from inky.auto import auto
                self.inky = auto(); self.mode = "inky"; return
            except Exception:
                pass
        self.mode = "preview"

    def show_stage(self, stage, level, battery=None):
        return self._push(render_stage_card(stage, level, battery))

    def show_splash(self, name="MANTIS"):
        return self._push(render_splash(name=name))

    def show_message(self, title, sub="", **kw):
        return self._push(render_message(title, sub, **kw))

    def show_about(self, snap, version):
        return self._push(render_about(snap, version))

    def show_menu(self, menu, battery=None):
        return self._push(render_menu(menu, battery))

    def show_posture(self, snap):
        return self._push(render_posture(snap))

    def show(self, snap, bob=0, battery=None, sleep_screen=False):
        img = render_sleep(snap, battery) if sleep_screen else \
            render_screen(snap, bob=bob, battery=battery)
        return self._push(img)

    def _push(self, img):
        if self.rotate:
            img = img.rotate(self.rotate, expand=True)
        if self.mode == "waveshare" and self.epd is not None:
            try:
                buf = self.epd.getbuffer(img)
                (self.epd.displayPartial if hasattr(self.epd, "displayPartial")
                 else self.epd.display)(buf)
                return "waveshare"
            except Exception:
                pass
        if self.mode == "inky" and self.inky is not None:
            try:
                self.inky.set_image(img.convert("P")); self.inky.show(); return "inky"
            except Exception:
                pass
        path = os.path.join(self.preview_dir, "screen.png")
        img.convert("L").resize((WIDTH * 3, HEIGHT * 3), Image.NEAREST).save(path)
        img.convert("L").save(os.path.join(self.preview_dir, "screen_1x.png"))
        return path

    def sleep(self):
        if self.mode == "waveshare" and self.epd is not None:
            try:
                self.epd.sleep()
            except Exception:
                pass


def _button_actions(engine):
    """Default physical-button behaviours."""
    from . import spells

    def cast_best():
        pet = engine.pet
        order = sorted(pet.unlocked_spells,
                       key=lambda s: spells.SPELLS[s].min_level, reverse=True)
        for sid in order:
            if pet.psyche >= spells.SPELLS[sid].psyche_cost:
                try:
                    spells.cast(engine, sid)
                except Exception:
                    pass
                return
        try:
            spells.cast(engine, "mind_reading")
        except Exception:
            pass

    def do_deed():
        for name in ("sever", "kidnap", "possess", "haunt"):
            spec = engine.DEEDS[name]
            if engine.pet.level >= spec["min_level"]:
                res = engine.deed(name)
                if res.get("ok"):
                    return
        engine.harvest()

    return {"feed": engine.feed, "meditate": engine.meditate,
            "pet": engine.pet_it, "cast": cast_best, "deed": do_deed}


def _button_combos(engine):
    """Two-button shortcuts (hold two buttons together)."""
    from . import upgrades as U

    def soothe():                                   # feed + pet
        with engine._lock:
            engine.pet.sanity = min(100.0, engine.pet.sanity + 30)
            engine.pet.darkness = max(0.0, engine.pet.darkness - 15)
        engine._award(5)
        engine.emit("combo", "You hold me. The screaming quiets. (soothed)")
        engine._after_action()

    def surge():                                    # feed + meditate
        with engine._lock:
            engine.pet.psyche = engine.psyche_cap()
            engine.pet.focus = min(100.0, engine.pet.focus + 40)
            engine.pet.energy = min(100.0, engine.pet.energy + 20)
        engine._hold_mood("overcharged", 5)
        engine.emit("combo", "PSYCHE surges to maximum! (power surge)")
        engine._after_action()

    def quick_buy():                                # meditate + deed
        affordable = [a for a in U.catalog(engine.pet)
                      if not a["maxed"] and a["affordable"]]
        if not affordable:
            engine.emit("combo", "Not enough souls to augment. (shop)")
            engine._after_action()
            return
        cheapest = min(affordable, key=lambda a: a["cost"])
        engine.buy_augment(cheapest["id"])

    return {
        frozenset({"feed", "pet"}): soothe,
        frozenset({"feed", "meditate"}): surge,
        frozenset({"meditate", "deed"}): quick_buy,
        frozenset({"cast", "deed"}): engine.harvest,
    }


IDLE_MOODS_FOR_BOB = {"watching", "listening", "observing", "serene", "content",
                      "tranquil", "meditative", "drowsy", "dreaming", "floating"}


def _power_off(engine, disp):
    """Safe shutdown: save, show a screen, then poweroff the device."""
    import shutil
    import subprocess
    try:
        engine.save()
        disp.show_message("POWER OFF", "saving... goodbye", eyes="closed",
                          pose="slump", fx="zzz")
        disp.sleep()
    except Exception:
        pass
    cmd = (["sudo", "poweroff"] if shutil.which("sudo") else ["poweroff"])
    try:
        subprocess.Popen(cmd)
    except Exception:
        pass


def _save_menu(engine, menu, live):
    """Persist the on-device menu to config.toml and apply what can change live."""
    from . import config as CFG
    eink_updates, battery_updates = menu.to_updates()
    try:
        CFG.update(engine.home, eink=eink_updates, battery=battery_updates)
    except Exception:
        pass
    for k in ("interval", "slideshow_interval", "low_battery", "sleep_below"):
        if k in eink_updates:
            try:
                live[k] = int(eink_updates[k])
            except (TypeError, ValueError):
                pass
    for k in ("animate", "slideshow"):
        if k in eink_updates:
            live[k] = bool(eink_updates[k])
    engine.emit("config", "Settings saved. (some apply on restart)")


def run_eink(engine, interval=30, rotate=0, driver="auto", autonomous=True,
             use_buttons=True, animate=True, pins=None,
             low_battery=20, sleep_below=6, splash=True,
             slideshow=True, slideshow_interval=25,
             poweroff_combo=True, poweroff_hold=3.0):
    from . import spells
    from .buttons import ButtonPad
    from .power import read_battery

    disp = EInkDisplay(home=engine.home, rotate=rotate, driver=driver)
    print(f"  [eink] driver = {disp.mode}")
    if disp.mode == "preview":
        print(f"  [eink] no panel found — previews -> {disp.preview_dir}")

    if splash:
        disp.show_splash("MANTIS")
        print("  [eink] boot splash")
        time.sleep(3)

    force = threading.Event()
    about_req = threading.Event()
    posture_req = threading.Event()
    menu_state = {"menu": None}
    # settings that can change live from the on-device menu
    live = {"interval": interval, "animate": animate, "slideshow": slideshow,
            "slideshow_interval": slideshow_interval, "low_battery": low_battery,
            "sleep_below": sleep_below}
    pad = None
    if use_buttons:
        def _wrap(fn):
            def run():
                fn()
                force.set()
            return run
        norm = _button_actions(engine)

        def _make_single(name):
            def run():
                m = menu_state["menu"]
                if m is not None:                   # ---- menu mode ----
                    if name == "meditate":
                        m.up()
                    elif name == "cast":
                        m.down()
                    elif name == "feed":
                        m.inc()
                    elif name == "pet":
                        m.dec()
                    elif name == "deed":
                        _save_menu(engine, m, live)
                        menu_state["menu"] = None
                else:
                    norm[name]()
                force.set()
            return run
        singles = {n: _make_single(n) for n in norm}
        combos = {k: _wrap(fn) for k, fn in _button_combos(engine).items()}
        combos[frozenset({"cast", "meditate"})] = _wrap(about_req.set)
        combos[frozenset({"feed", "cast"})] = _wrap(posture_req.set)
        combos[frozenset({"meditate", "pet"})] = _wrap(engine.toggle_mode)

        def _open_menu():
            from . import menu as MENU, config as CFG
            cur = CFG.load(engine.home)
            vals = dict(cur.get("eink", {}))
            vals["battery"] = cur.get("battery", {}).get("source", "auto")
            for k in ("interval", "slideshow_interval", "low_battery", "sleep_below"):
                vals.setdefault(k, live[k])
            for k in ("animate", "slideshow"):
                vals.setdefault(k, live[k])
            vals.setdefault("rotate", rotate)
            vals.setdefault("driver", driver)
            vals.setdefault("splash", splash)
            vals.setdefault("poweroff_combo", poweroff_combo)
            menu_state["menu"] = MENU.SettingsMenu(vals)
            force.set()

        hold_combos = {frozenset({"pet", "deed"}): _open_menu}
        if poweroff_combo:
            hold_combos[frozenset({"cast", "pet"})] = lambda: _power_off(engine, disp)

        def _hold_start(pair):
            try:
                if pair == frozenset({"cast", "pet"}):
                    disp.show_message("POWER OFF?", "keep holding to shut down",
                                      eyes="wide", pose="reach")
                else:
                    disp.show_message("SETTINGS?", "keep holding to open",
                                      eyes="normal", pose="point")
            except Exception:
                pass

        def _hold_cancel(pair):
            force.set()     # redraw whatever screen we were on

        pad = ButtonPad(singles, combos=combos, pins=pins,
                        hold_combos=hold_combos, hold_seconds=poweroff_hold,
                        on_hold_start=_hold_start, on_hold_cancel=_hold_cancel)
        print(f"  [eink] buttons = {'ON  (' + pad.describe() + ')' if pad.available else 'not found'}")

    batt = read_battery(engine.home)
    print(f"  [eink] battery = {batt['source'] + ' ' + str(int(batt['percent'])) + '%' if batt else 'none'}"
          f"   (low<{low_battery}%, hibernate<{sleep_below}%)")

    from . import stages as ST
    from . import __version__ as _VER
    import random as _rnd
    last_sig = None
    last_auto = last_tick = last_bob = last_batt = last_slide = 0.0
    frame = 0
    bob_px = 0
    hibernating = False
    last_level = engine.pet.level
    stage_until = 0.0
    slide_until = 0.0
    about_until = 0.0
    posture_until = 0.0
    try:
        while True:
            now = time.time()
            if now - last_batt > 25:
                batt = read_battery(engine.home)
                last_batt = now
            pct = batt["percent"] if batt else None

            # ---- on-device SETTINGS menu (hold pet+deed) ------------------- #
            if menu_state["menu"] is not None:
                m = menu_state["menu"]
                sig_m = ("menu", m.signature())
                if sig_m != last_sig or force.is_set():
                    disp.show_menu(m, battery=batt)
                    last_sig = sig_m
                    force.clear()
                force.wait(timeout=0.2)
                continue

            # ---- on-device ABOUT screen (hold cast+meditate) --------------- #
            if about_req.is_set():
                about_req.clear()
                disp.show_about(engine.snapshot(), _VER)
                print("  [eink] about screen")
                about_until = now + 6
                last_sig = None
            if now < about_until:
                if force.wait(timeout=0.3):
                    force.clear(); about_until = 0.0
                continue

            # ---- on-device SECURITY POSTURE screen (feed+cast) ------------- #
            if posture_req.is_set():
                posture_req.clear()
                disp.show_posture(engine.snapshot())
                print("  [eink] posture screen")
                posture_until = now + 6
                last_sig = None
            if now < posture_until:
                if force.wait(timeout=0.3):
                    force.clear(); posture_until = 0.0
                continue

            # ---- evolution reveal: show the stage card on level-up --------- #
            if engine.pet.level != last_level:
                stg = ST.stage_for(engine.pet.level)
                disp.show_stage(stg, engine.pet.level, battery=batt)
                print(f"  [eink] EVOLVED -> LV{engine.pet.level} {stg['label']}")
                last_level = engine.pet.level
                stage_until = now + 7
                last_sig = None
            if now < stage_until:
                if force.wait(timeout=0.3):
                    force.clear()
                    stage_until = 0.0        # a button press returns to the status screen
                continue

            # ---- hibernation (deep sleep) ---------------------------------- #
            if pct is not None and pct <= live["sleep_below"] and not (batt and batt.get("charging")):
                if not hibernating:
                    engine.tick(); engine.save()
                    disp.show(engine.snapshot(), battery=batt, sleep_screen=True)
                    disp.sleep()
                    hibernating = True
                    last_sig = None
                    print(f"  [eink] HIBERNATING at {int(pct)}% battery")
                # check back infrequently; wake instantly if a button is pressed
                if force.wait(timeout=60):
                    force.clear()
                continue
            if hibernating:
                hibernating = False
                print("  [eink] waking from hibernation")

            # low-battery: slow down + stop the idle animation
            low = pct is not None and pct <= live["low_battery"]
            eff_interval = live["interval"] * (4 if low else 1)
            do_anim = live["animate"] and not low

            if now - last_tick > min(5, eff_interval):
                engine.tick()
                if autonomous and not low and now - last_auto > max(eff_interval, 40):
                    spells.autonomous_sense(engine)   # passive sensing (both modes)
                    engine.auto_activity()            # active mode: perform an activity
                    last_auto = now
                engine.save()
                last_tick = now

            snap = engine.snapshot()
            from . import personality as _P
            mood_cluster = _P.MOODS.get(snap["mood"], {}).get("c", "idle")
            calm = mood_cluster in ("idle", "content") and not low

            # ---- idle slideshow: a calm pet flips through its unlocked stages - #
            if now < slide_until:
                if force.wait(timeout=0.3):
                    force.clear(); slide_until = 0.0; last_sig = None
                continue
            if live["slideshow"] and calm and now - last_slide > live["slideshow_interval"]:
                lvl = _rnd.randint(1, min(engine.pet.level, ST.MAX_STAGE))
                stg = ST.stage_for(lvl)
                disp.show_stage(stg, lvl, battery=batt)
                print(f"  [eink] slideshow -> LV{lvl} {stg['label']}")
                last_slide = now
                slide_until = now + 6
                last_sig = None
                continue

            draw_bob = False
            if do_anim and calm and now - last_bob > 3.0:
                frame ^= 1
                bob_px = 2 if frame else 0
                last_bob = now
                draw_bob = True

            sig = (snap["mood"], snap["phrase"], snap["level"], int(snap["psyche_pct"]),
                   int(snap["xp_pct"]), int(snap["darkness"]),
                   int(pct) if pct is not None else -1)
            if sig != last_sig or force.is_set() or draw_bob:
                where = disp.show(snap, bob=bob_px, battery=batt)
                if sig != last_sig or force.is_set():
                    print(f"  [eink] refreshed ({snap['mood']}) -> {where}")
                last_sig = sig
                force.clear()
            time.sleep(0.15)
    except KeyboardInterrupt:
        pass
    finally:
        engine.save(); disp.sleep()
        if pad is not None:
            pad.cleanup()
        print("\n  The mask goes dark. I am always listening...\n")


# --------------------------------------------------------------------------- #
# Preview baking
# --------------------------------------------------------------------------- #
def bake_faces(outdir, scale=3, moods=None):
    from . import personality as P
    os.makedirs(outdir, exist_ok=True)
    demo = {"name": "Mantis", "level": 66, "level_cap": 100,
            "rank": "Phantom", "psyche_pct": 74, "xp_pct": 48, "darkness": 61,
            "souls": 128, "infamy": 44,
            "stats": {"kills": 13, "kidnappings": 9, "possessions": 27,
                      "networks_sensed": 88}}
    moods = moods or list(P.MOODS.keys())
    paths = []
    for mood in moods:
        meta = P.MOODS[mood]
        snap = dict(demo, mood=mood, phrase=P.pick(meta["p"]),
                    sprite={"eyes": meta["eyes"], "aura": meta["aura"],
                            "pose": meta["pose"], "fx": meta["fx"]})
        img = render_screen(snap).convert("L").resize(
            (WIDTH * scale, HEIGHT * scale), Image.NEAREST)
        p = os.path.join(outdir, f"mantis_{mood}.png")
        img.save(p); paths.append(p)
    # contact sheet of a representative set
    show = moods[:24]
    cols = 4
    rows = (len(show) + cols - 1) // cols
    cw, ch, pad = WIDTH, HEIGHT, 6
    sheet = Image.new("L", (cols * cw + pad * (cols + 1), rows * ch + pad * (rows + 1)), WHITE)
    for i, mood in enumerate(show):
        meta = P.MOODS[mood]
        snap = dict(demo, mood=mood, phrase=mood.upper().replace("_", " "),
                    sprite={"eyes": meta["eyes"], "aura": meta["aura"],
                            "pose": meta["pose"], "fx": meta["fx"]})
        tile = render_screen(snap).convert("L")
        r, c = divmod(i, cols)
        sheet.paste(tile, (pad + c * (cw + pad), pad + r * (ch + pad)))
    sp = os.path.join(outdir, "contact_sheet.png")
    sheet.save(sp); paths.append(sp)
    return paths


def bake_stages(outdir, scale=3, levels=None):
    """Bake the 50 evolution stage cards + a contact-sheet gallery."""
    from . import stages as ST
    os.makedirs(outdir, exist_ok=True)
    levels = levels or [s["lvl"] for s in ST.STAGES]
    paths = []
    for lvl in levels:
        stg = ST.stage_for(lvl)
        img = render_stage_card(stg, lvl).convert("L").resize(
            (WIDTH * scale, HEIGHT * scale), Image.NEAREST)
        p = os.path.join(outdir, f"stage_{lvl:02d}_{stg['key']}.png")
        img.save(p); paths.append(p)
    # 5-wide contact sheet (like the reference sheets)
    cols = 5
    rows = (len(levels) + cols - 1) // cols
    cw, ch, pad = WIDTH, HEIGHT, 4
    sheet = Image.new("L", (cols * cw + pad * (cols + 1), rows * ch + pad * (rows + 1)), WHITE)
    for i, lvl in enumerate(levels):
        stg = ST.stage_for(lvl)
        tile = render_stage_card(stg, lvl).convert("L")
        r, c = divmod(i, cols)
        sheet.paste(tile, (pad + c * (cw + pad), pad + r * (ch + pad)))
    sp = os.path.join(outdir, "stage_gallery.png")
    sheet.save(sp); paths.append(sp)
    return paths
