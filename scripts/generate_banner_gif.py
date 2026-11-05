from __future__ import annotations

from io import BytesIO
import math
from pathlib import Path
import xml.etree.ElementTree as ET

import cairosvg
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
SVG_PATH = ROOT / "profile" / "banner.svg"
GIF_PATH = ROOT / "profile" / "banner.gif"
SVG_NS = "http://www.w3.org/2000/svg"
BACKGROUND = "#111111"
TRACE = "#b8b8b8"
CONNECTOR = "#484848"
WIDTH = 1200
HEIGHT = 280

MAIN_ROUTE = [(758, 176), (850, 176), (850, 114), (982, 114), (1082, 114), (1082, 188), (1135, 188)]
BRANCHES = [
    [(982, 114), (982, 72), (1096, 72)],
    [(850, 114), (850, 222), (944, 222)],
]
NODES = [(758, 176), (850, 114), (982, 114), (1082, 188), (1096, 72), (944, 222)]


def render_static_banner() -> Image.Image:
    ET.register_namespace("", SVG_NS)
    root = ET.fromstring(SVG_PATH.read_bytes())
    for group_id in ("diagram-lines", "diagram-nodes"):
        group = root.find(f".//{{{SVG_NS}}}g[@id='{group_id}']")
        if group is not None:
            root.remove(group)
    svg = ET.tostring(root, encoding="utf-8")
    png = cairosvg.svg2png(bytestring=svg, output_width=WIDTH, output_height=HEIGHT)
    return Image.open(BytesIO(png)).convert("RGB")


def draw_progress(draw: ImageDraw.ImageDraw, points: list[tuple[int, int]], progress: float, color: str) -> None:
    lengths = [math.dist(start, end) for start, end in zip(points, points[1:])]
    remaining = max(0.0, min(1.0, progress)) * sum(lengths)
    drawn = [points[0]]
    for start, end, length in zip(points, points[1:], lengths):
        if remaining >= length:
            drawn.append(end)
            remaining -= length
            continue
        if remaining > 0:
            ratio = remaining / length
            drawn.append((round(start[0] + (end[0] - start[0]) * ratio), round(start[1] + (end[1] - start[1]) * ratio)))
        break
    if len(drawn) > 1:
        draw.line(drawn, fill=color, width=2, joint="curve")


def draw_nodes(image: Image.Image, radius: int) -> None:
    draw = ImageDraw.Draw(image)
    for x, y in NODES:
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=BACKGROUND, outline=TRACE, width=2)


def main() -> None:
    base = render_static_banner()
    frames: list[Image.Image] = [base.copy()]
    durations = [80]

    for step in range(1, 17):
        frame = base.copy()
        draw_progress(ImageDraw.Draw(frame), MAIN_ROUTE, step / 16, TRACE)
        frames.append(frame)
        durations.append(65)

    for step in range(1, 9):
        frame = base.copy()
        draw_progress(ImageDraw.Draw(frame), MAIN_ROUTE, 1, TRACE)
        for branch in BRANCHES:
            draw_progress(ImageDraw.Draw(frame), branch, step / 8, TRACE)
        frames.append(frame)
        durations.append(65)

    for radius in (3, 5, 5):
        frame = base.copy()
        draw_progress(ImageDraw.Draw(frame), MAIN_ROUTE, 1, TRACE)
        for branch in BRANCHES:
            draw_progress(ImageDraw.Draw(frame), branch, 1, TRACE)
        draw_nodes(frame, radius)
        frames.append(frame)
        durations.append(90)

    for color in ("#898989", CONNECTOR):
        frame = base.copy()
        draw_progress(ImageDraw.Draw(frame), MAIN_ROUTE, 1, color)
        for branch in BRANCHES:
            draw_progress(ImageDraw.Draw(frame), branch, 1, color)
        draw_nodes(frame, 5)
        frames.append(frame)
        durations.append(100)

    final = base.copy()
    draw_progress(ImageDraw.Draw(final), MAIN_ROUTE, 1, CONNECTOR)
    for branch in BRANCHES:
        draw_progress(ImageDraw.Draw(final), branch, 1, CONNECTOR)
    draw_nodes(final, 5)
    frames.append(final)
    durations.append(2500)

    palette_frames = [frame.convert("P", palette=Image.Palette.ADAPTIVE, colors=256, dither=Image.Dither.NONE) for frame in frames]
    palette_frames[0].save(
        GIF_PATH,
        save_all=True,
        append_images=palette_frames[1:],
        duration=durations,
        disposal=2,
        optimize=True,
    )


if __name__ == "__main__":
    main()
