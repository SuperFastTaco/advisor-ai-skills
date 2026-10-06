#!/usr/bin/env python3
"""Build a visual advisor brand reference from Markdown rules and local assets.

Requires Python 3.10+, reportlab, and Pillow. All work is local. See
../references/pdf-builder.md for the optional asset manifest schema.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from io import BytesIO
import json
import ntpath
import os
from pathlib import Path
import re
import sys
import tempfile
import warnings
from xml.sax.saxutils import escape


class BuildError(Exception):
    """An input or output problem the caller can correct."""


@dataclass
class Asset:
    category: str
    identifier: str
    name: str
    status: str
    usage: str
    source: str
    path: Path
    filename: str
    pixels: bytes
    width: int
    height: int


STATUSES = {"confirmed", "extracted", "observed", "proposed"}
RASTER_FORMATS = {"PNG", "JPEG", "WEBP", "TIFF", "BMP", "GIF"}
ABSOLUTE_LABEL = re.compile(r"(?:^|\s)(?:/\S+|[A-Za-z]:[\\/]\S+|\\\\\S+)")


def read_text(path: Path, label: str) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise BuildError(f"{label} must be UTF-8 text.") from exc
    except OSError as exc:
        raise BuildError(f"Cannot read {label}: {exc.strerror or exc}") from exc


def display_text(value, field: str, default: str = "Not provided.") -> str:
    if value is None:
        return default
    if not isinstance(value, str) or not value.strip():
        raise BuildError(f"{field} must be a nonempty string.")
    if ABSOLUTE_LABEL.search(value):
        raise BuildError(f"{field} must use a human-readable label, not an absolute file path.")
    return value.strip()


def identifier(value, field: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", value):
        raise BuildError(f"{field} must be an id of 1-64 letters, digits, hyphens, or underscores.")
    return value


def status(value, field: str) -> str:
    if not isinstance(value, str) or value not in STATUSES:
        raise BuildError(f"{field} must be confirmed, extracted, observed, or proposed.")
    return value


def hex_color(value, field: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
        raise BuildError(f"{field} must be a six-digit color such as #16324F.")
    return value.upper()


def keys(record: dict, allowed: set[str], field: str) -> None:
    unexpected = set(record) - allowed
    if unexpected:
        raise BuildError(f"Unknown field in {field}: {', '.join(sorted(unexpected))}")


def prepare_image(path: Path, label: str, background: str | None) -> tuple[bytes, int, int]:
    from PIL import Image, ImageDraw, ImageOps, UnidentifiedImageError

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(path) as original:
                if original.format not in RASTER_FORMATS:
                    raise BuildError(f"{label} is not a supported raster image; supply a raster preview.")
                original.load()
                image = ImageOps.exif_transpose(original).convert("RGBA")
        width, height = image.size
        if width < 1 or height < 1:
            raise BuildError(f"{label} has no image pixels.")
        # A checkerboard represents transparency, rather than inventing a brand
        # background. A manifest may instead specify an approved preview color.
        if background is not None:
            canvas = Image.new("RGBA", image.size, background)
            canvas.alpha_composite(image)
            image = canvas.convert("RGB")
        elif image.getchannel("A").getextrema()[0] < 255:
            canvas = Image.new("RGBA", image.size, "#B8B8B8")
            painter = ImageDraw.Draw(canvas)
            tile = max(8, min(width, height) // 16)
            for y in range(0, height, tile):
                for x in range(0, width, tile):
                    if (x // tile + y // tile) % 2:
                        painter.rectangle((x, y, x + tile - 1, y + tile - 1), fill="#D4D4D4")
            canvas.alpha_composite(image)
            image = canvas.convert("RGB")
        else:
            image = image.convert("RGB")
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue(), width, height
    except BuildError:
        raise
    except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise BuildError(f"Cannot load image {label}; check that it is a complete supported raster file.") from exc


def load_manifest(path: Path | None) -> tuple[str | None, list[dict], list[Asset]]:
    if path is None:
        return None, [], []
    try:
        manifest = json.loads(read_text(path, "asset manifest"))
    except json.JSONDecodeError as exc:
        raise BuildError(f"Asset manifest is invalid JSON at line {exc.lineno}.") from exc
    if not isinstance(manifest, dict):
        raise BuildError("Asset manifest must be a JSON object.")
    keys(manifest, {"brand_name", "colors", "logos", "photos"}, "manifest")
    brand = display_text(manifest.get("brand_name"), "brand_name", default="") or None
    colors: list[dict] = []
    assets: list[Asset] = []
    seen: set[str] = set()
    for category in ("colors", "logos", "photos"):
        records = manifest.get(category, [])
        if not isinstance(records, list):
            raise BuildError(f"{category} must be an array.")
        for index, record in enumerate(records):
            field = f"{category}[{index}]"
            if not isinstance(record, dict):
                raise BuildError(f"{field} must be an object.")
            allowed = {"id", "name", "status", "usage", "source", "hex"} if category == "colors" else {
                "id", "name", "status", "usage", "source", "path", "background"
            }
            keys(record, allowed, field)
            item_id = identifier(record.get("id"), f"{field}.id")
            if item_id in seen:
                raise BuildError(f"Duplicate asset id: {item_id}")
            seen.add(item_id)
            common = {
                "id": item_id,
                "name": display_text(record.get("name"), f"{field}.name", default=item_id),
                "status": status(record.get("status"), f"{field}.status"),
                "usage": display_text(record.get("usage"), f"{field}.usage"),
                "source": display_text(record.get("source"), f"{field}.source"),
            }
            if category == "colors":
                common["hex"] = hex_color(record.get("hex"), f"{field}.hex")
                colors.append(common)
                continue
            relative = record.get("path")
            if not isinstance(relative, str) or not relative.strip() or "\0" in relative:
                raise BuildError(f"{field}.path must be a local relative image path.")
            if Path(relative).is_absolute() or ntpath.isabs(relative):
                raise BuildError(f"{field}.path must be relative to the asset manifest.")
            image_path = path.parent / relative
            if not image_path.is_file():
                raise BuildError(f"Missing image for {item_id}: {Path(relative).name}")
            background = hex_color(record["background"], f"{field}.background") if "background" in record else None
            pixels, width, height = prepare_image(image_path, f"{item_id} ({image_path.name})", background)
            assets.append(Asset(
                category=category,
                identifier=item_id,
                name=common["name"],
                status=common["status"],
                usage=common["usage"],
                source=common["source"],
                path=image_path.resolve(),
                filename=display_text(image_path.name, f"{field} filename"),
                pixels=pixels,
                width=width,
                height=height,
            ))
    return brand, colors, assets


def rules_title(text: str) -> str:
    for line in text.splitlines():
        heading = re.match(r"^#\s+(.+?)\s*$", line)
        if heading:
            return heading.group(1)
    return "Advisor brand guide"


def select_font(explicit: Path | None, text: str) -> str:
    import reportlab
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    candidates = [explicit] if explicit is not None else [
        Path(reportlab.__file__).parent / "fonts" / "Vera.ttf",
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"),
        Path("/Library/Fonts/Arial Unicode.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("C:/Windows/Fonts/arial.ttf"),
    ]
    required = {ord(character) for character in text if character not in "\n\r\t"}
    smallest_missing: set[int] | None = None
    for index, path in enumerate(candidates):
        if not path.is_file():
            continue
        try:
            font = TTFont(f"BrandText{index}", str(path))
        except Exception as exc:
            if explicit is not None:
                raise BuildError("Cannot load --font as a TrueType font.") from exc
            continue
        missing = required - set(font.face.charToGlyph)
        if not missing:
            pdfmetrics.registerFont(font)
            return font.fontName
        if smallest_missing is None or len(missing) < len(smallest_missing):
            smallest_missing = missing
    if smallest_missing is None:
        raise BuildError("No usable TrueType font found. Supply one with --font.")
    codes = ", ".join(f"U+{value:04X}" for value in sorted(smallest_missing)[:10])
    raise BuildError(f"Available fonts cannot display all source characters ({codes}). Supply a covering TrueType font with --font.")


def wrap_code(line: str, font: str, size: float, width: float) -> list[str]:
    from reportlab.pdfbase.pdfmetrics import stringWidth

    line = line.expandtabs(4)
    if not line:
        return [""]
    lines: list[str] = []
    while line:
        if stringWidth(line, font, size) <= width:
            lines.append(line)
            break
        low, high = 1, len(line)
        while low < high:
            middle = (low + high + 1) // 2
            if stringWidth(line[:middle], font, size) <= width:
                low = middle
            else:
                high = middle - 1
        lines.append(line[:low])
        line = line[low:]
    return lines


def markdown_flowables(text: str, styles: dict, font: str, width: float) -> list:
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import Paragraph, Preformatted, Spacer

    result: list = []
    in_code: str | None = None
    for line in text.splitlines():
        fence = re.match(r"^\s*(`{3,}|~{3,})", line)
        if fence:
            marker = fence.group(1)[0]
            in_code = None if in_code == marker else marker
            result.append(Preformatted(line, styles["code"]))
        elif in_code:
            wrapped = "\n".join(wrap_code(line, font, 8.5, width - 12))
            result.append(Preformatted(wrapped, styles["code"]))
        elif not line.strip():
            if not (result and isinstance(result[-1], Paragraph) and getattr(result[-1].style, "keepWithNext", False)):
                result.append(Spacer(1, 4))
        else:
            heading = re.match(r"^\s{0,3}(#{1,6})\s+(.+?)\s*$", line)
            bullet = re.match(r"^(\s*)([-+*]|\d+[.)])\s+(.+)$", line)
            if heading:
                style = styles["section"] if len(heading.group(1)) <= 2 else styles["subsection"]
                result.append(Paragraph(escape(heading.group(2)), style))
            elif bullet:
                indent = min(len(bullet.group(1).expandtabs(4)) * 4, 48)
                style = ParagraphStyle("BrandNestedBullet", parent=styles["bullet"], leftIndent=14 + indent, bulletIndent=2 + indent)
                result.append(Paragraph(escape(bullet.group(3)), style, bulletText=bullet.group(2)))
            else:
                result.append(Paragraph(escape(line), styles["body"]))
    return result


def write_pdf(output: Path, title: str, rules: str, colors: list[dict], assets: list[Asset], font_path: Path | None) -> None:
    from reportlab.lib import colors as pdf_colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.platypus import Flowable, Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    visible = [title, rules, "Brand reference Color palette Logos Photos Not provided Status Confirmed Extracted Observed Proposed Usage Source ID File Page 0123456789"]
    for color in colors:
        visible.extend(color.values())
    for asset in assets:
        visible.extend([asset.identifier, asset.name, asset.status, asset.usage, asset.source, asset.filename])
    font = select_font(font_path, "\n".join(visible))
    ink = pdf_colors.HexColor("#17212D")
    muted = pdf_colors.HexColor("#536171")
    styles = {
        "title": ParagraphStyle("BrandTitle", fontName=font, fontSize=25, leading=30, textColor=ink, spaceAfter=6),
        "subtitle": ParagraphStyle("BrandSubtitle", fontName=font, fontSize=12, leading=17, textColor=muted, spaceAfter=20),
        "section": ParagraphStyle("BrandSection", fontName=font, fontSize=16, leading=21, textColor=ink, spaceBefore=16, spaceAfter=10, keepWithNext=True),
        "subsection": ParagraphStyle("BrandSubsection", fontName=font, fontSize=12, leading=17, textColor=ink, spaceBefore=11, spaceAfter=6, keepWithNext=True),
        "body": ParagraphStyle("BrandBody", fontName=font, fontSize=10.5, leading=15, textColor=ink, spaceAfter=5, splitLongWords=True),
        "small": ParagraphStyle("BrandSmall", fontName=font, fontSize=9, leading=13, textColor=muted, spaceAfter=4, splitLongWords=True),
        "bullet": ParagraphStyle("BrandBullet", fontName=font, bulletFontName=font, fontSize=10.5, leading=15, textColor=ink, leftIndent=14, bulletIndent=2, spaceAfter=5, splitLongWords=True),
        "code": ParagraphStyle("BrandCode", fontName=font, fontSize=8.5, leading=12, textColor=ink, leftIndent=6, spaceAfter=2),
    }
    width = letter[0] - 108
    story: list = [Paragraph(escape(title), styles["title"]), Paragraph("Brand reference", styles["subtitle"])]

    class Swatch(Flowable):
        def __init__(self, color: str):
            super().__init__()
            self.width, self.height = 88, 56
            self.color = pdf_colors.HexColor(color)

        def draw(self) -> None:
            self.canv.setFillColor(self.color)
            self.canv.setStrokeColor(pdf_colors.HexColor("#B7BEC7"))
            self.canv.rect(0, 0, self.width, self.height, fill=1, stroke=1)

    story.append(Paragraph("Color palette", styles["section"]))
    if not colors:
        story.append(Paragraph("Brand colors were not provided.", styles["body"]))
    for color in colors:
        caption = [
            Paragraph(escape(color["name"]), styles["subsection"]),
            Paragraph(escape(f'{color["hex"]} | ID: {color["id"]}'), styles["body"]),
            Paragraph(escape(f'Status: {color["status"].capitalize()}'), styles["small"]),
        ]
        table = Table([[Swatch(color["hex"]), caption]], colWidths=[108, width - 108], hAlign="LEFT")
        table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
        story.extend([table, Paragraph(escape(f'Usage: {color["usage"]}'), styles["body"]), Paragraph(escape(f'Source: {color["source"]}'), styles["small"]), Spacer(1, 9)])

    for category, heading, absent in (
        ("logos", "Logos", "Logo files were not provided."),
        ("photos", "Photos", "Photo files were not provided."),
    ):
        items = [asset for asset in assets if asset.category == category]
        if not items:
            story.append(KeepTogether([Paragraph(heading, styles["section"]), Paragraph(absent, styles["body"])]))
        for index, asset in enumerate(items):
            max_height = 170 if category == "logos" else 225
            scale = min((width - 24) / asset.width, max_height / asset.height)
            image = Image(BytesIO(asset.pixels), width=asset.width * scale, height=asset.height * scale)
            frame = Table([[image]], colWidths=[width], hAlign="LEFT")
            frame.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("BOX", (0, 0), (-1, -1), 0.5, pdf_colors.HexColor("#D3D8DE")), ("TOPPADDING", (0, 0), (-1, -1), 12), ("BOTTOMPADDING", (0, 0), (-1, -1), 12)]))
            section_heading = [Paragraph(heading, styles["section"])] if index == 0 else []
            story.append(KeepTogether(section_heading + [
                Paragraph(escape(asset.name), styles["subsection"]),
                Paragraph(escape(f"ID: {asset.identifier} | File: {asset.filename} | Status: {asset.status.capitalize()}"), styles["small"]),
                frame,
            ]))
            story.extend([Spacer(1, 8), Paragraph(escape(f"Usage: {asset.usage}"), styles["body"]), Paragraph(escape(f"Source: {asset.source}"), styles["small"]), Spacer(1, 10)])

    # A trailing spacer can spill onto a fresh page immediately before this
    # explicit break, creating a page that contains only its footer.
    while story and isinstance(story[-1], Spacer):
        story.pop()
    story.append(PageBreak())
    story.extend(markdown_flowables(rules, styles, font, width))

    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        handle, temporary_name = tempfile.mkstemp(prefix=".brand-guide-", suffix=".pdf", dir=output.parent)
        os.close(handle)
    except OSError as exc:
        raise BuildError(f"Cannot prepare output: {exc.strerror or exc}") from exc
    temporary = Path(temporary_name)
    try:
        document = SimpleDocTemplate(str(temporary), pagesize=letter, leftMargin=54, rightMargin=54, topMargin=48, bottomMargin=48, title="Advisor brand reference", author="", subject="Visual identity and brand guidance", creator="Brand guide builder")

        def footer(canvas, doc) -> None:
            canvas.saveState()
            canvas.setFont(font, 8)
            canvas.setFillColor(muted)
            canvas.drawRightString(letter[0] - 54, 27, f"Page {doc.page}")
            canvas.restoreState()

        def invariant_canvas(*args, **kwargs):
            kwargs["invariant"] = True
            return Canvas(*args, **kwargs)

        document.build(story, onFirstPage=footer, onLaterPages=footer, canvasmaker=invariant_canvas)
        os.replace(temporary, output)
    except OSError as exc:
        raise BuildError(f"Cannot write output: {exc.strerror or exc}") from exc
    except Exception as exc:
        raise BuildError(f"Cannot lay out the guide: {exc}") from exc
    finally:
        temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rules", required=True, type=Path, help="Markdown brand rules file")
    parser.add_argument("--assets", type=Path, help="Optional JSON manifest of local colors, logos, and photos")
    parser.add_argument("--output", required=True, type=Path, help="Destination PDF path")
    parser.add_argument("--font", type=Path, help="Optional TrueType font covering all source characters")
    args = parser.parse_args(argv)
    try:
        if args.rules.suffix.lower() != ".md":
            raise BuildError("--rules must be a Markdown file with a .md extension.")
        if args.output.suffix.lower() != ".pdf":
            raise BuildError("--output must have a .pdf extension.")
        if args.output.resolve() == args.rules.resolve() or (args.assets is not None and args.output.resolve() == args.assets.resolve()):
            raise BuildError("Output must not replace the rules or asset manifest.")
        rules = read_text(args.rules, "brand rules")
        if not rules.strip():
            raise BuildError("Brand rules must not be empty.")
        try:
            import reportlab  # noqa: F401
            import PIL  # noqa: F401
        except ImportError as exc:
            raise BuildError("Missing dependency: install reportlab and Pillow in this Python environment.") from exc
        brand, colors, assets = load_manifest(args.assets)
        if any(asset.path == args.output.resolve() for asset in assets):
            raise BuildError("Output must not replace a supplied image.")
        title = brand or rules_title(rules)
        write_pdf(args.output, title, rules, colors, assets, args.font)
    except BuildError as exc:
        parser.exit(2, f"error: {exc}\n")
    print(f"Created brand guide: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
