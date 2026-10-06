# Build the visual brand-reference PDF

Use the bundled helper after the advisor's rules and available assets have been assembled. It works locally and requires Python 3.10+, `reportlab`, and `Pillow`:

```bash
python3 -m pip install reportlab Pillow
python3 scripts/build_brand_pdf.py \
  --rules /path/to/Advisor-branding-rules.md \
  --assets /path/to/brand-assets.json \
  --output /path/to/Advisor-branding-rules.pdf
```

Run the command from this skill's folder, or use the full path to its script. `--assets` is optional. With no manifest, the PDF states that colors, logos, and photos were not provided, then includes the rules. Do not use missing sections to invent a brand identity.

The PDF shows actual color swatches and proportional image previews before the complete Markdown rules. Keep manifest captions and source labels concise; retain full asset restrictions and usage details in the Markdown rules. Basic Markdown headings and bullets become readable headings and lists; other Markdown, including inline emphasis, remains literal. Code blocks retain their text and indentation, with long lines wrapped. The helper does not rewrite the source rules. Page numbers, filenames, and asset IDs make the reference easy to use.

## Asset manifest

The manifest is a UTF-8 JSON object with four supported fields: optional `brand_name` and optional `colors`, `logos`, and `photos` arrays. Omitted arrays mean those assets were not provided. Item order is retained.

```json
{
  "brand_name": "Harbor Example Planning",
  "colors": [
    {
      "id": "primary-navy",
      "name": "Navy",
      "hex": "#16324F",
      "status": "confirmed",
      "usage": "Primary headings and logo lettering.",
      "source": "Advisor-approved brand sheet"
    },
    {
      "id": "accent-gold",
      "name": "Gold",
      "hex": "#C99B45",
      "status": "extracted",
      "usage": "Accent lines observed on the website.",
      "source": "Website header"
    }
  ],
  "logos": [
    {
      "id": "primary-logo",
      "name": "Primary horizontal logo",
      "path": "assets/logo-preview.png",
      "status": "confirmed",
      "usage": "Use on light backgrounds.",
      "source": "Logo supplied by the advisor",
      "background": "#FFFFFF"
    }
  ],
  "photos": [
    {
      "id": "advisor-portrait",
      "name": "Advisor portrait",
      "path": "assets/advisor-portrait.jpg",
      "status": "confirmed",
      "usage": "About page and advisor introduction materials.",
      "source": "Portrait selected by the advisor"
    }
  ]
}
```

All items require `id` and `status`. IDs must be unique across the three arrays and contain 1-64 letters, digits, hyphens, or underscores, beginning with a letter or digit. Optional `name` defaults to the ID. Optional `usage` and `source` display as “Not provided.” when absent. Use human-readable names and sources; absolute file paths are rejected in displayed manifest labels.

Statuses describe the evidence or approval recorded during the brand workflow:

- `confirmed`: the advisor approved this item or its use.
- `extracted`: an explicit specification or item taken from supplied materials, awaiting confirmation when needed.
- `observed`: visually inferred from supplied materials, including approximate colors sampled from pixels.
- `proposed`: a recommendation for advisor review.

The helper renders the supplied status; it does not infer approval or change extracted items to confirmed.

For a sampled color, use `observed` and say in its `source` or `usage` that it is an approximate pixel sample. Do not label a sampled approximation as an official extracted specification.

Each color also requires `hex`, exactly `#` followed by six hexadecimal digits. Its name, hex value, ID, status, usage, and source accompany a swatch filled with that exact color.

Each logo or photo requires `path`, a local path relative to the manifest file. Absolute image paths are rejected; relative parent paths such as `../assets/logo.png` are supported. The PDF displays only the image's filename, never its absolute path. Supported raster formats are PNG, JPEG, WebP, TIFF, BMP, and GIF. A static preview uses the first frame of animated or multi-frame files. Camera orientation is applied and image proportions are retained; images are not cropped.

Optional image `background` is a six-digit hex color used behind the preview. Transparent previews otherwise use a neutral checkerboard to show the transparent areas. This preview backdrop is not a new brand color or an inferred logo usage rule.

Keep vector originals such as SVG, EPS, AI, or PDF in the advisor's asset folder and provide an actual raster preview for this helper. Identify the original file and any usage restrictions in the Markdown rules. The helper does not convert vector artwork or download images.

## Input checks

The helper validates the manifest, color values, and every specified image before writing the output. Missing or corrupt images, unsupported formats, unknown manifest fields, duplicate IDs, invalid statuses, and invalid colors produce a clear error instead of being silently skipped. The output replaces an existing PDF only after a successful build; the source rules, manifest, and images cannot be overwritten.

The default embedded font handles ordinary Latin text and typographic quotes. Additional installed fonts are tried when needed. If a character cannot be displayed, the build fails instead of dropping it. Supply a TrueType font covering all required characters with `--font /path/to/font.ttf` when necessary. PDF metadata uses a generic title and contains no source paths. Text deliberately written into the rules is preserved, so keep private paths and information out of customer-facing rules.
