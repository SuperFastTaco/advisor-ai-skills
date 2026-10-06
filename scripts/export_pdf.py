#!/usr/bin/env python3
"""Export Markdown source text or a skill folder to a readable PDF.

Requires Python 3.10+ and reportlab. Markdown syntax remains literal; this is
a reading copy, not a Markdown renderer or a native skill installation.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import sys
import tempfile


class ExportError(Exception):
    """A source, font, or output problem the caller can correct."""


def read_markdown(path: Path, label: str) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ExportError(f"Markdown must be UTF-8: {label}") from exc
    except OSError as exc:
        raise ExportError(f"Cannot read {label}: {exc.strerror or exc}") from exc


def collect_sources(
    source: Path, output: Path
) -> tuple[list[tuple[str, str]], list[str], bool]:
    if not source.exists():
        raise ExportError("Input does not exist.")
    if source.is_file():
        if source.suffix.lower() != ".md":
            raise ExportError("Input file must have a .md extension.")
        if source.resolve() == output.resolve():
            raise ExportError("Output must not replace the source file.")
        return [(source.name, read_markdown(source, source.name))], [], False
    if not source.is_dir():
        raise ExportError("Input must be a Markdown file or a skill directory.")
    entrypoint = source / "SKILL.md"
    if not entrypoint.is_file():
        raise ExportError("Skill directory must contain SKILL.md.")

    markdown: list[Path] = []
    resources: list[str] = []
    for path in sorted(source.rglob("*"), key=lambda item: item.relative_to(source).as_posix()):
        relative = path.relative_to(source)
        if any(part.startswith(".") for part in relative.parts):
            continue
        if path.is_symlink():
            raise ExportError(f"Symbolic links are not supported: {relative.as_posix()}")
        if not path.is_file() or path.resolve() == output.resolve():
            continue
        if path.suffix.lower() == ".md":
            if path != entrypoint:
                markdown.append(path)
        else:
            resources.append(relative.as_posix())

    ordered = [entrypoint, *markdown]
    sources = [
        (path.relative_to(source).as_posix(), read_markdown(path, path.relative_to(source).as_posix()))
        for path in ordered
    ]
    return sources, resources, True


def source_title(text: str, fallback: str) -> str:
    in_fence: str | None = None
    in_frontmatter = text.startswith("---\n")
    for index, line in enumerate(text.splitlines()):
        if in_frontmatter:
            if index and line.strip() == "---":
                in_frontmatter = False
            continue
        fence = re.match(r"^\s*(`{3,}|~{3,})", line)
        if fence:
            marker = fence.group(1)[0]
            in_fence = None if in_fence == marker else marker
            continue
        if in_fence is None:
            heading = re.match(r"^#\s+(.+?)\s*$", line)
            if heading:
                return heading.group(1)
    return fallback


def select_font(reportlab_module, explicit: Path | None, text: str) -> str:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    if explicit is not None:
        candidates = [explicit]
    else:
        candidates = [
            Path(reportlab_module.__file__).parent / "fonts" / "Vera.ttf",
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf"),
            Path("/Library/Fonts/Arial Unicode.ttf"),
            Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
            Path("C:/Windows/Fonts/arial.ttf"),
        ]
    required = {ord(character) for character in text if character not in "\n\r\t"}
    missing: set[int] = set()
    found_font = False
    for index, path in enumerate(candidates):
        if not path.is_file():
            continue
        try:
            name = f"ExportText{index}"
            font = TTFont(name, str(path))
        except Exception as exc:
            if explicit is not None:
                raise ExportError("Cannot load --font as a TrueType font.") from exc
            continue
        found_font = True
        unsupported = required - set(font.face.charToGlyph)
        if not unsupported:
            pdfmetrics.registerFont(font)
            return name
        if not missing or len(unsupported) < len(missing):
            missing = unsupported

    if explicit is not None and not explicit.is_file():
        raise ExportError("The --font file does not exist.")
    if not found_font:
        raise ExportError("No usable TrueType font found. Supply one with --font.")
    codes = ", ".join(f"U+{code:04X}" for code in sorted(missing)[:10])
    raise ExportError(
        f"Available fonts cannot display all source characters ({codes}). "
        "Supply a TrueType font covering these characters with --font."
    )


def wrap_line(line: str, font: str, size: float, width: float) -> list[str]:
    """Wrap without dropping source characters or collapsing whitespace."""
    from reportlab.pdfbase.pdfmetrics import stringWidth

    line = line.expandtabs(4)
    if not line:
        return [""]
    wrapped: list[str] = []
    while line:
        if stringWidth(line, font, size) <= width:
            wrapped.append(line)
            break
        low, high = 1, len(line)
        while low < high:
            middle = (low + high + 1) // 2
            if stringWidth(line[:middle], font, size) <= width:
                low = middle
            else:
                high = middle - 1
        split = low
        space = line.rfind(" ", 0, split + 1)
        if space > split // 2:
            split = space + 1
        wrapped.append(line[:split])
        line = line[split:]
    return wrapped


def write_pdf(
    output: Path,
    title: str,
    sources: list[tuple[str, str]],
    resources: list[str],
    is_skill: bool,
    font_path: Path | None,
) -> None:
    try:
        import reportlab
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except ImportError as exc:
        raise ExportError("Missing dependency: install reportlab in this Python environment.") from exc

    introduction = "Reading edition of the skill instructions." if is_skill else ""
    bundle_note = (
        "For native installation or any listed non-Markdown resources, use the original "
        "skill folder. This PDF does not execute scripts."
    )
    resource_heading = "Non-Markdown bundle resources (contents not included)"
    all_text = "\n".join(
        [title, introduction, bundle_note if is_skill else "", resource_heading, "Page 0123456789"]
        + [f"Source: {label}\n{text}" for label, text in sources]
        + resources
    )
    font = select_font(reportlab, font_path, all_text)
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(prefix=".pdf-export-", suffix=".pdf", dir=output.parent)
        os.close(descriptor)
    except OSError as exc:
        raise ExportError(f"Cannot prepare output: {exc.strerror or exc}") from exc

    temporary = Path(temporary_name)
    try:
        document = canvas.Canvas(str(temporary), pagesize=letter, invariant=True, pageCompression=1)
        # Metadata is deliberately generic: no absolute source or output paths.
        document.setTitle("Markdown text export")
        document.setAuthor("")
        document.setSubject("Selectable source text; Markdown syntax retained")
        document.setCreator("Advisor skill PDF exporter")
        page_width, page_height = letter
        margin = 54.0
        text_width = page_width - 2 * margin
        y = page_height - margin
        page_number = 1

        def footer() -> None:
            document.setFont(font, 8)
            document.setFillColorRGB(0.35, 0.35, 0.35)
            document.drawRightString(page_width - margin, 28, f"Page {page_number}")

        def next_page() -> None:
            nonlocal y, page_number
            footer()
            document.showPage()
            page_number += 1
            y = page_height - margin

        def draw_text(text: str, size: float = 9.5, leading: float = 13.0) -> None:
            nonlocal y
            for original in text.splitlines() or [""]:
                for line in wrap_line(original, font, size, text_width):
                    if y < margin + leading:
                        next_page()
                    document.setFont(font, size)
                    document.setFillColorRGB(0.08, 0.08, 0.08)
                    document.drawString(margin, y, line)
                    y -= leading

        def gap(points: float = 10) -> None:
            nonlocal y
            y -= points

        draw_text(title, size=18, leading=23)
        gap()
        if is_skill:
            draw_text(introduction)
            gap(5)
            draw_text(bundle_note)
            gap(16)
        for index, (label, text) in enumerate(sources):
            if index:
                next_page()
            if is_skill:
                draw_text(f"Source: {label}", size=11, leading=16)
                gap(7)
            draw_text(text)
        if resources:
            gap(18)
            draw_text(resource_heading, size=11, leading=16)
            gap(5)
            for resource in resources:
                draw_text(f"- {resource}")
        footer()
        document.save()
        os.replace(temporary, output)
    except OSError as exc:
        raise ExportError(f"Cannot write output: {exc.strerror or exc}") from exc
    finally:
        temporary.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Markdown file or skill directory containing SKILL.md")
    parser.add_argument("--output", required=True, type=Path, help="Destination PDF path")
    parser.add_argument("--font", type=Path, help="Optional TrueType font covering the source characters")
    args = parser.parse_args(argv)
    try:
        if args.output.suffix.lower() != ".pdf":
            raise ExportError("Output must have a .pdf extension.")
        sources, resources, is_skill = collect_sources(args.source, args.output)
        title = source_title(sources[0][1], "Skill source export" if is_skill else args.source.stem)
        write_pdf(args.output, title, sources, resources, is_skill, args.font)
    except ExportError as exc:
        parser.exit(2, f"error: {exc}\n")
    print(f"Exported {len(sources)} Markdown file(s) to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
