"""Color renderer for the Pimoroni HyperPixel (and any RGB screen).

The e-ink path draws 1-bit mono; this draws a full-color MANTIS UI at HyperPixel
resolution (default 800x480; HyperPixel 4.0 Square is 720x720). It reuses the
same gas-mask figure art, colorized, and adds colored bars, the posture grade,
academy rank, evolution stage, and the personalized phrase.

On a real HyperPixel you run the browser UI full-screen (kiosk) pointed at
``/color`` — that is the robust path for a DSI/DPI panel. This module also bakes
PNG frames (served at ``/color.png``) and can best-effort blit to ``/dev/fb0``.
"""

from __future__ import annotations

import os
from typing import Any, Dict, Tuple

from PIL import Image, ImageDraw

from . import eink

# palette (RGB) — red & black theme, matches the web dashboard
BG = (8, 3, 3)
PANEL = (22, 10, 11)
PANEL2 = (16, 7, 8)
GREEN = (255, 59, 59)       # primary accent is red now
MAG = (255, 31, 73)         # brand crimson
CYAN = (255, 122, 74)       # secondary orange-red
AMBER = (255, 176, 32)
RED = (255, 43, 43)
PURPLE = (255, 92, 122)
GREY = (154, 115, 120)
INK = (243, 207, 199)
WHITE = (255, 240, 236)

try:
    import numpy as _np
except Exception:
    _np = None


def _font(size):
    return eink._font(size)


def _colorize(mono: Image.Image, ink: Tuple[int, int, int]) -> Image.Image:
    """The drawn (black) figure pixels become `ink`; white background -> transparent."""
    g = mono.convert("L")
    if _np is not None:
        a = _np.array(g)
        fig = a < 128                       # the figure ink (black)
        out = _np.zeros((a.shape[0], a.shape[1], 4), dtype="uint8")
        out[..., 0] = ink[0]
        out[..., 1] = ink[1]
        out[..., 2] = ink[2]
        out[..., 3] = _np.where(fig, 255, 0)
        return Image.fromarray(out, "RGBA")
    rgba = Image.new("RGBA", g.size, (0, 0, 0, 0))
    mask = g.point(lambda v: 255 if v < 128 else 0).convert("L")
    rgba.paste(ink + (255,), (0, 0), mask)
    return rgba


def _bar(d, x, y, w, h, pct, color, label=None, fsmall=None):
    d.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, fill=(6, 8, 14),
                        outline=(40, 48, 66))
    fw = int((w - 4) * max(0, min(100, pct)) / 100)
    if fw > 4:
        d.rounded_rectangle([x + 2, y + 2, x + 2 + fw, y + h - 2], radius=(h - 4) // 2,
                            fill=color)
    if label and fsmall:
        d.text((x, y - 15), label, font=fsmall, fill=GREY)


def _grade_color(grade: str):
    return {"A": GREEN, "B": CYAN, "C": AMBER, "D": RED, "F": RED}.get(grade, GREY)


# theme palettes for the color (HyperPixel) renderer: (primary, brand, secondary,
# figure tint, panel fill, panel outline, bg wash base, wash step)
THEMES = {
    "red":   dict(GREEN=(255, 59, 59), MAG=(255, 31, 73), CYAN=(255, 122, 74),
                  AMBER=(255, 176, 32), RED=(255, 43, 43), PURPLE=(255, 92, 122),
                  GREY=(154, 115, 120), INK=(243, 207, 199), WHITE=(255, 240, 236),
                  FIG=(255, 80, 72), PFILL=(20, 6, 8), POUT=(80, 20, 24),
                  BG=(8, 3, 3), WASH=(10, 4, 5), STEP=(14, 5, 6)),
    "mono":  dict(GREEN=(255, 255, 255), MAG=(255, 255, 255), CYAN=(210, 210, 210),
                  AMBER=(255, 255, 255), RED=(230, 230, 230), PURPLE=(200, 200, 200),
                  GREY=(138, 138, 138), INK=(255, 255, 255), WHITE=(255, 255, 255),
                  FIG=(240, 240, 240), PFILL=(14, 14, 14), POUT=(90, 90, 90),
                  BG=(0, 0, 0), WASH=(6, 6, 6), STEP=(10, 10, 10)),
    "green": dict(GREEN=(107, 255, 107), MAG=(255, 58, 208), CYAN=(53, 230, 255),
                  AMBER=(255, 194, 75), RED=(255, 77, 77), PURPLE=(176, 107, 255),
                  GREY=(133, 145, 163), INK=(199, 245, 184), WHITE=(240, 255, 240),
                  FIG=(150, 255, 170), PFILL=(6, 18, 12), POUT=(16, 60, 30),
                  BG=(10, 13, 20), WASH=(10, 13, 20), STEP=(6, 8, 14)),
    "amber": dict(GREEN=(255, 176, 32), MAG=(255, 140, 26), CYAN=(255, 208, 96),
                  AMBER=(255, 207, 90), RED=(255, 106, 42), PURPLE=(255, 169, 77),
                  GREY=(154, 132, 86), INK=(255, 227, 166), WHITE=(255, 240, 210),
                  FIG=(255, 190, 70), PFILL=(20, 13, 2), POUT=(90, 60, 10),
                  BG=(10, 7, 0), WASH=(12, 8, 2), STEP=(16, 11, 4)),
}


def active_theme() -> str:
    try:
        from . import config as CFG, engine as EN
        return (CFG.load(EN.default_home()).get("web", {}) or {}).get("theme", "red")
    except Exception:
        return "red"


def render(snap: Dict[str, Any], size: Tuple[int, int] = (800, 480),
           theme: str = None) -> Image.Image:
    W, H = size
    pal = THEMES.get(theme or active_theme(), THEMES["red"])
    GREEN, MAG, CYAN = pal["GREEN"], pal["MAG"], pal["CYAN"]
    AMBER, RED, PURPLE = pal["AMBER"], pal["RED"], pal["PURPLE"]
    GREY, INK, WHITE = pal["GREY"], pal["INK"], pal["WHITE"]
    _gc = {"A": GREEN, "B": CYAN, "C": AMBER, "D": RED, "F": RED}
    img = Image.new("RGB", (W, H), pal["BG"])
    d = ImageDraw.Draw(img)
    wb, ws = pal["WASH"], pal["STEP"]
    for i in range(H):
        t = i / H
        d.line([(0, i), (W, i)], fill=(int(wb[0] + ws[0] * t), int(wb[1] + ws[1] * t),
                                       int(wb[2] + ws[2] * t)))

    f_title = _font(max(22, W // 26))
    f_big = _font(max(18, W // 34))
    f_med = _font(max(14, W // 48))
    f_sm = _font(max(12, W // 60))

    pad = int(W * 0.03)
    # ---- figure panel (left) ---------------------------------------------- #
    fw = int(W * 0.40)
    d.rounded_rectangle([pad, pad, fw, H - pad], radius=18, fill=pal["PFILL"],
                        outline=pal["POUT"], width=2)
    # draw a big portrait figure, then colorize to a CRT ghost in the theme hue
    fig_mono = Image.new("1", (200, 320), 255)
    eink.place_figure(fig_mono, (8, 2, 184, 312), snap.get("sprite", {}),
                      keys=eink._fig_keys(snap))
    panel_w = fw - pad - 16
    panel_h = H - 2 * pad - 16
    scale = min(panel_w / fig_mono.width, panel_h / fig_mono.height)
    fig = fig_mono.resize((max(1, int(fig_mono.width * scale)),
                           max(1, int(fig_mono.height * scale))), Image.NEAREST)
    figc = _colorize(fig, pal["FIG"])
    fx = pad + (fw - pad - figc.width) // 2
    fy = pad + (H - 2 * pad - figc.height) // 2
    img.paste(figc, (max(pad + 4, fx), max(pad + 4, fy)), figc)

    # ---- right column ----------------------------------------------------- #
    rx = fw + pad
    y = pad
    name = snap.get("name", "Mantis")
    d.text((rx, y), name, font=f_title, fill=WHITE)
    y += f_title.size + 4
    d.text((rx, y), f"LV {snap.get('level',1)}/{snap.get('level_cap',100)}  "
                    f"{snap.get('rank','')}", font=f_med, fill=PURPLE)
    y += f_med.size + 4
    stage = (snap.get("stage") or {}).get("label", "")
    acad = (snap.get("academy") or {}).get("tier", "")
    d.text((rx, y), f"> {stage}", font=f_sm, fill=CYAN)
    y += f_sm.size + 2
    d.text((rx, y), f"academy: {acad}", font=f_sm, fill=GREY)
    y += f_sm.size + 14

    bw = W - rx - pad
    for label, key, color in (("PSYCHE", "psyche_pct", MAG), ("XP", "xp_pct", AMBER),
                              ("DARKNESS", "darkness", RED)):
        _bar(d, rx, y, bw, 16, snap.get(key, 0), color, label, f_sm)
        y += 34

    # needs row
    needs = snap.get("needs", {})
    nb = (bw - 12) // 2
    for i, (lbl, color) in enumerate((("hunger", GREEN), ("energy", CYAN),
                                      ("focus", AMBER), ("sanity", RED))):
        col = i % 2
        row = i // 2
        bx = rx + col * (nb + 12)
        by = y + row * 26
        _bar(d, bx, by + 10, nb, 10, needs.get(lbl, 0), color)
        d.text((bx, by), lbl, font=f_sm, fill=GREY)
    y += 60

    # posture badge + souls/stats
    p = snap.get("posture", {}) or {}
    gc = _gc.get(p.get("grade", "?"), GREY)
    d.rounded_rectangle([rx, y, rx + 40, y + 40], radius=8, outline=gc, width=2)
    gf = _font(26)
    d.text((rx + 10, y + 4), p.get("grade", "?"), font=gf, fill=gc)
    d.text((rx + 52, y + 2), "SECURITY", font=f_sm, fill=GREY)
    d.text((rx + 52, y + 18), f"POSTURE {('' if p.get('score') is None else p['score'])}",
           font=f_sm, fill=INK)
    st = snap.get("stats", {})
    d.text((rx + 170, y + 2), f"SOULS {snap.get('souls',0)}", font=f_sm, fill=PURPLE)
    d.text((rx + 170, y + 18), f"nets {st.get('networks_sensed',0)}  "
                               f"spells {st.get('spells_cast',0)}", font=f_sm, fill=GREY)

    # ---- phrase bar (bottom, full width) ---------------------------------- #
    d.rounded_rectangle([pad, H - 46, W - pad, H - pad], radius=10, fill=pal["PFILL"],
                        outline=pal["POUT"])
    phrase = snap.get("phrase", "...")
    d.text((pad + 14, H - 38), f'“{phrase}”', font=f_med, fill=CYAN)
    return img


def render_splash(size=(800, 480), name="MANTIS", theme: str = None) -> Image.Image:
    W, H = size
    pal = THEMES.get(theme or active_theme(), THEMES["red"])
    MAG, CYAN = pal["MAG"], pal["CYAN"]
    img = Image.new("RGB", (W, H), pal["BG"])
    d = ImageDraw.Draw(img)
    wb, ws = pal["WASH"], pal["STEP"]
    for i in range(H):
        t = i / H
        d.line([(0, i), (W, i)], fill=(int(wb[0] + ws[0] * t), int(wb[1] + ws[1] * t),
                                       int(wb[2] + ws[2] * t)))
    fig_mono = Image.new("1", (eink.WIDTH, eink.HEIGHT), 255)
    eink.draw_figure(fig_mono, (0, 0, eink.WIDTH, eink.HEIGHT - 10),
                     {"eyes": "glow", "aura": "waves", "pose": "float", "fx": "none"})
    scale = (H * 0.62) / eink.HEIGHT
    fig = fig_mono.resize((int(fig_mono.width * scale), int(fig_mono.height * scale)),
                          Image.NEAREST)
    figc = _colorize(fig, pal["FIG"])
    img.paste(figc, ((W - figc.width) // 2, int(H * 0.22)), figc)
    f_logo = _font(max(40, W // 14))
    letters = " ".join(name.upper())
    lw = d.textlength(letters, font=f_logo)
    d.text(((W - lw) // 2, int(H * 0.06)), letters, font=f_logo, fill=MAG)
    f_sm = _font(max(14, W // 44))
    tag = "I can read your mind..."
    tw = d.textlength(tag, font=f_sm)
    d.text(((W - tw) // 2, H - 44), tag, font=f_sm, fill=CYAN)
    return img


def bake_preview(outdir: str, snap: Dict[str, Any], size=(800, 480)) -> str:
    os.makedirs(outdir, exist_ok=True)
    p = os.path.join(outdir, "color_preview.png")
    render(snap, size).save(p)
    return p


# --------------------------------------------------------------------------- #
# Best-effort Linux framebuffer blit (for headless HyperPixel without a browser)
# --------------------------------------------------------------------------- #
def blit_framebuffer(img: Image.Image, fb: str = "/dev/fb0",
                     size: Tuple[int, int] = None) -> bool:
    try:
        if size:
            img = img.resize(size)
        # HyperPixel framebuffer is typically RGB565, little-endian
        rgb = img.convert("RGB")
        if _np is None:
            return False
        a = _np.array(rgb).astype("uint16")
        r = (a[..., 0] >> 3) << 11
        g = (a[..., 1] >> 2) << 5
        b = (a[..., 2] >> 3)
        packed = (r | g | b).astype("<u2")
        with open(fb, "wb") as fh:
            fh.write(packed.tobytes())
        return True
    except Exception:
        return False
