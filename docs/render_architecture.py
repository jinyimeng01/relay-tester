#!/usr/bin/env python3
"""Render dark-tech architecture diagrams for the GitHub README."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parent / "img"
OUT.mkdir(parents=True, exist_ok=True)

BG = (8, 12, 20)
PANEL = (16, 24, 38)
PANEL2 = (22, 32, 50)
STROKE = (56, 78, 110)
CYAN = (56, 189, 248)
GREEN = (52, 211, 153)
RED = (248, 113, 113)
ORANGE = (251, 146, 60)
AMBER = (252, 211, 77)
MUTED = (148, 163, 184)
WHITE = (241, 245, 249)
DIM = (100, 116, 139)


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/msyhbd.ttc" if bold else "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def rounded(draw: ImageDraw.ImageDraw, xy, fill, outline=None, r=16, width=1):
    draw.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=width)


def shadow_panel(img: Image.Image, xy, r=16, fill=PANEL, outline=STROKE):
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    x0, y0, x1, y1 = xy
    d.rounded_rectangle((x0 + 4, y0 + 6, x1 + 4, y1 + 6), radius=r, fill=(0, 0, 0, 70))
    img.alpha_composite(overlay)
    draw = ImageDraw.Draw(img)
    rounded(draw, xy, fill=fill, outline=outline, r=r, width=2)
    return draw


def text(draw, xy, s, size=18, fill=WHITE, bold=False, anchor="lt"):
    draw.text(xy, s, font=font(size, bold), fill=fill, anchor=anchor)


def arrow(draw, a, b, color=CYAN, w=3):
    draw.line([a, b], fill=color, width=w)
    x0, y0 = a
    x1, y1 = b
    # simple chevron at end
    if abs(x1 - x0) >= abs(y1 - y0):
        dir_ = 1 if x1 >= x0 else -1
        draw.polygon(
            [(x1, y1), (x1 - 10 * dir_, y1 - 6), (x1 - 10 * dir_, y1 + 6)],
            fill=color,
        )
    else:
        dir_ = 1 if y1 >= y0 else -1
        draw.polygon(
            [(x1, y1), (x1 - 6, y1 - 10 * dir_), (x1 + 6, y1 - 10 * dir_)],
            fill=color,
        )


def badge(draw, xy, label, fill, fg=BG):
    x, y = xy
    w = 8 * len(label) + 22
    rounded(draw, (x, y, x + w, y + 22), fill=fill, r=11)
    text(draw, (x + w / 2, y + 11), label, size=12, fill=fg, bold=True, anchor="mm")


def header_bar(img, title, subtitle):
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, img.width, 92), fill=(10, 16, 28))
    draw.rectangle((0, 90, img.width, 94), fill=CYAN)
    text(draw, (36, 22), title, size=28, bold=True)
    text(draw, (36, 58), subtitle, size=16, fill=MUTED)
    text(draw, (img.width - 36, 46), "relay-tester", size=16, fill=CYAN, bold=True, anchor="rm")


def save(img: Image.Image, name: str):
    path = OUT / name
    img.convert("RGB").save(path, "PNG", optimize=True)
    print("wrote", path, img.size)


def diagram_architecture():
    img = Image.new("RGBA", (1400, 820), BG + (255,))
    header_bar(img, "Protocol-layer architecture", "OpenAI-compatible relay  ·  six-probe fingerprint plane")
    draw = ImageDraw.Draw(img)

    # client
    shadow_panel(img, (48, 140, 280, 430), fill=PANEL)
    text(draw, (164, 168), "CLIENT", size=13, fill=CYAN, bold=True, anchor="mm")
    text(draw, (164, 200), "OpenAI SDK", size=20, bold=True, anchor="mm")
    for i, line in enumerate(["chat.completions", "model = sold name", "max_tokens / temp", "optional image_url"]):
        text(draw, (68, 240 + i * 32), "·  " + line, size=15, fill=MUTED)
    text(draw, (164, 390), "benchmark.py", size=14, fill=GREEN, bold=True, anchor="mm")
    text(draw, (164, 412), "probe_suite.py", size=14, fill=GREEN, bold=True, anchor="mm")

    # gateway
    shadow_panel(img, (360, 140, 1040, 760), fill=(14, 22, 36), outline=(36, 64, 96))
    text(draw, (700, 162), "RELAY GATEWAY  ·  new-api / one-api", size=18, bold=True, fill=AMBER, anchor="mm")
    text(draw, (700, 188), "string layer is fully attacker-controlled", size=14, fill=MUTED, anchor="mm")

    layers = [
        (200, "L1  Routing", "tier → upstream pool", "split / cheap source", CYAN),
        (300, "L2  Rewrite", "inject system prompt", "sold-name echo", ORANGE),
        (400, "L3  Params", "ignore max_tokens", "strip reasoning", RED),
        (500, "L4  Metering", "usage pass-through", "or re-pack tokens", AMBER),
        (600, "L5  Protocol", "error fingerprint", "new_api_error", GREEN),
    ]
    for y, title, a, b, color in layers:
        shadow_panel(img, (392, y, 1008, y + 84), fill=PANEL2, outline=color)
        draw.rectangle((392, y, 400, y + 84), fill=color)
        text(draw, (420, y + 16), title, size=18, bold=True, fill=color)
        text(draw, (420, y + 48), a + "   ·   " + b, size=15, fill=MUTED)

    # upstream
    shadow_panel(img, (1120, 180, 1352, 360), fill=PANEL)
    text(draw, (1236, 208), "UPSTREAM A", size=13, fill=GREEN, bold=True, anchor="mm")
    text(draw, (1236, 240), "official API", size=18, bold=True, anchor="mm")
    text(draw, (1236, 274), "deepseek-chat", size=14, fill=MUTED, anchor="mm")
    text(draw, (1236, 300), "deepseek-reasoner", size=14, fill=MUTED, anchor="mm")

    shadow_panel(img, (1120, 400, 1352, 620), fill=PANEL)
    text(draw, (1236, 428), "UPSTREAM B", size=13, fill=RED, bold=True, anchor="mm")
    text(draw, (1236, 462), "unknown pool", size=18, bold=True, anchor="mm")
    text(draw, (1236, 498), "vision sidecar", size=14, fill=ORANGE, anchor="mm")
    text(draw, (1236, 524), "older checkpoint", size=14, fill=MUTED, anchor="mm")
    text(draw, (1236, 550), "cross-family mix", size=14, fill=MUTED, anchor="mm")

    arrow(draw, (280, 250), (360, 250), CYAN)
    arrow(draw, (1040, 270), (1120, 270), GREEN)
    arrow(draw, (1040, 500), (1120, 500), RED)
    text(draw, (320, 228), "HTTP", size=12, fill=CYAN, bold=True, anchor="mm")

    save(img, "architecture.png")


def diagram_hero():
    img = Image.new("RGBA", (1400, 420), BG + (255,))
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, 1400, 6), fill=CYAN)
    text(draw, (48, 36), "relay-tester", size=16, fill=CYAN, bold=True)
    text(draw, (48, 78), "Protocol-layer autopsy", size=36, bold=True)
    text(draw, (48, 128), "for OpenAI-compatible LLM relays", size=22, fill=MUTED)
    text(draw, (48, 176), "Marketing strings are attacker-controlled.", size=16, fill=WHITE)
    text(draw, (48, 202), "Tokenizer counts, knowledge cutoffs and usage schemas are not.", size=16, fill=MUTED)
    metrics = [
        ("6", "probes"),
        ("5", "gateway layers"),
        ("30%", "tokenizer delta"),
        ("T=0", "similarity"),
    ]
    for i, (n, lab) in enumerate(metrics):
        x = 48 + i * 200
        shadow_panel(img, (x, 270, x + 180, 380), fill=PANEL, outline=STROKE, r=14)
        text(draw, (x + 90, 308), n, size=28, bold=True, fill=CYAN, anchor="mm")
        text(draw, (x + 90, 348), lab, size=14, fill=MUTED, anchor="mm")
    text(draw, (1352, 46), "MIT  ·  Python", size=14, fill=MUTED, anchor="rm")
    save(img, "hero.png")


def diagram_probes():
    img = Image.new("RGBA", (1400, 860), BG + (255,))
    header_bar(img, "Six-probe fingerprint plane", "Ask what it claims  ·  measure what it is  ·  prove if it is real")
    draw = ImageDraw.Draw(img)

    groups = [
        (48, "Q1  CLAIMS", CYAN, [
            ("P1", "Identity pentad", "name / cutoff / context / API", "cutoff lives in weights"),
            ("U", "Usage schema", "reasoning_tokens present?", "R1-class API structure"),
            ("E", "Error fingerprint", "new_api_error / 403 [1M]", "gateway family, free"),
        ]),
        (500, "Q2  ACTUAL", ORANGE, [
            ("P2", "Tokenizer", "same text -> prompt_tokens", "delta >= 30%  =>  different family"),
            ("P3", "Capability", "same DP, n=20 → 845", "expensive tier fails = inversion"),
            ("P4", "Prompt leak", "unified identity copy", "injected system prompt"),
        ]),
        (952, "Q3  REAL?", GREEN, [
            ("P5", "Vision", "PIL HELLO-42 canvas", "text-only that sees = divert"),
            ("P6", "Similarity", "T=0 same prompt", ">80% overlap = same backend"),
        ]),
    ]
    for x, title, color, probes in groups:
        shadow_panel(img, (x, 130, x + 400, 830), fill=PANEL, outline=color)
        draw.rectangle((x, 130, x + 400, 178), fill=color)
        text(draw, (x + 200, 154), title, size=18, bold=True, fill=BG, anchor="mm")
        for i, (pid, name, how, rule) in enumerate(probes):
            y = 200 + i * 200
            shadow_panel(img, (x + 20, y, x + 380, y + 180), fill=PANEL2, outline=STROKE)
            badge(draw, (x + 36, y + 18), pid, color, BG)
            text(draw, (x + 110, y + 28), name, size=18, bold=True)
            text(draw, (x + 36, y + 70), how, size=15, fill=MUTED)
            text(draw, (x + 36, y + 104), rule, size=14, fill=WHITE)

    save(img, "probes.png")


def diagram_pipeline():
    img = Image.new("RGBA", (1400, 520), BG + (255,))
    header_bar(img, "15-minute detection pipeline", "Do not buy a tier until the matrix closes")
    draw = ImageDraw.Draw(img)

    steps = [
        ("01", "Ingest", "key · base URL\nsold names", CYAN),
        ("02", "Benchmark", "3-tier latency\nmax_tokens audit", ORANGE),
        ("03", "Fingerprint", "six probes\ncross-model", GREEN),
        ("04", "Matrix", "tokenizer Δ\ncutoff conflict", AMBER),
        ("05", "Verdict", "mix / skin\ninversion / divert", RED),
    ]
    for i, (num, title, body, color) in enumerate(steps):
        x = 48 + i * 270
        shadow_panel(img, (x, 150, x + 240, 430), fill=PANEL, outline=color)
        draw.ellipse((x + 88, 172, x + 152, 236), outline=color, width=3)
        text(draw, (x + 120, 204), num, size=20, bold=True, fill=color, anchor="mm")
        text(draw, (x + 120, 268), title, size=22, bold=True, anchor="mm")
        for j, line in enumerate(body.split("\n")):
            text(draw, (x + 120, 318 + j * 28), line, size=15, fill=MUTED, anchor="mm")
        if i < len(steps) - 1:
            arrow(draw, (x + 248, 290), (x + 262, 290), color)

    text(draw, (700, 470), "Gold standard: tokenizer count  ×  knowledge cutoff  ×  usage schema", size=16, fill=CYAN, anchor="mm")
    save(img, "pipeline.png")


def diagram_case():
    img = Image.new("RGBA", (1400, 640), BG + (255,))
    header_bar(img, "Case  1.19848845.xyz   ·   2026-09-05", "Three sold names  ·  three tokenizers  ·  inverted pricing")
    draw = ImageDraw.Draw(img)

    rows = [
        ("deepseek-v4-pro", "899", "2024-07", "130  FAIL", "≈ R1-class", RED, "most expensive, worst math"),
        ("deepseek-v4-flash", "308", "2024-06", "845  PASS", "≈ V3 / chat", GREEN, "cheap, not weaker"),
        ("v4-flash-vision-exp", "587", "2026-01", "845  PASS", "≈ V3.2-exp VL", CYAN, "real vision + reasoning=213"),
    ]
    headers = ["SOLD NAME", "TOKENS", "CUTOFF", "DP n=20", "INFER", "NOTE"]
    xs = [48, 360, 520, 700, 920, 1140]
    for x, h in zip(xs, headers):
        text(draw, (x, 130), h, size=13, fill=MUTED, bold=True)

    draw.line((48, 158, 1352, 158), fill=STROKE, width=1)
    for i, (name, tok, cut, dp, infer, color, note) in enumerate(rows):
        y = 180 + i * 130
        shadow_panel(img, (48, y, 1352, y + 112), fill=PANEL, outline=color)
        text(draw, (70, y + 38), name, size=20, bold=True, fill=color)
        text(draw, (360, y + 38), tok, size=28, bold=True, fill=WHITE)
        text(draw, (520, y + 42), cut, size=18, fill=AMBER)
        text(draw, (700, y + 42), dp, size=18, fill=RED if "FAIL" in dp else GREEN)
        text(draw, (920, y + 42), infer, size=18, fill=WHITE)
        text(draw, (1140, y + 42), note, size=15, fill=MUTED)

    text(draw, (700, 600), "[1M] suffix → 403    ·    max_tokens 300 → 1024    ·    all three can see a PIL image", size=15, fill=MUTED, anchor="mm")
    save(img, "case-matrix.png")


if __name__ == "__main__":
    diagram_hero()
    diagram_architecture()
    diagram_probes()
    diagram_pipeline()
    diagram_case()
