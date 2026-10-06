# Advisor AI Skills

A library created by Kevin Nuber to help independent financial advisors and their teams run and grow their practices.

Each skill guides an agent through a specific advisor workflow and produces a usable result, such as a documented process, an ideal-client profile, or a workshop follow-up plan.

## Get started

Read [Start Here](guides/start-here.md) for customer instructions. Open the complete [Advisor Brand Guide skill folder](skills/advisor-brand-guide/) for its instructions and bundled resources. For downloadable PDF editions and customer handouts, see [the latest release](https://github.com/SuperFastTaco/advisor-ai-skills/releases/latest).

## First skill: Advisor Brand Guide

[Advisor Brand Guide](skills/advisor-brand-guide/SKILL.md) first requests and scans the advisor's logos, website, brochures, and photos, then asks only about missing information or conflicts. It creates `Advisor-branding-rules.md` and `Advisor-branding-rules.pdf`, covering mission, values, services, ideal clients, positioning, voice, color palette, typography, logos, imagery, and other marketing rules. The PDF embeds color swatches and available logos and photos. It works without prior AI experience; unavailable materials remain clearly identified.

Customer instructions are in [Start Here](guides/start-here.md). The skill instructions and the advisor's finished brand guide are different documents: the first creates the second.

In Codex, after installation, start with:

> Use $advisor-brand-guide to review my website, logos, brochures, and photos first, ask only missing questions, and create Advisor-branding-rules.md and a visual PDF for my agents.

## Two ways to use a skill

**GitHub folder:** The complete skill lives in `skills/<skill-name>/`, with `SKILL.md` and any references, scripts, or assets it needs. An agent with a supported skill installer can install that folder.

**PDF:** A readable edition is generated from the same Markdown source. An advisor can attach it to an agent that supports reading PDFs and ask it to follow the workflow. The PDF does not install the skill or make it persistently discoverable. Executable helpers and other assets still require the accompanying folder.

The Markdown source is maintained first; the PDF is regenerated from it.

## Author a skill

Read [AUTHORING.md](AUTHORING.md), then adapt [the skill template](templates/skill-template.md). Put the completed instructions in `skills/<skill-name>/SKILL.md`.

Keep each skill self-contained. The advisor supplies their own business details, preferences, tools, and relevant examples; the skill must work without Kevin's Personal Brain.

## Export a PDF

The helper requires Python 3.10 or later and `reportlab`:

```sh
python3 -m pip install reportlab
python3 scripts/export_pdf.py skills/advisor-brand-guide --output output/pdf/advisor-brand-guide-skill.pdf
```

It can also export an individual Markdown document:

```sh
python3 scripts/export_pdf.py AUTHORING.md --output output/pdf/advisor-skill-authoring-guide.pdf
```

The export preserves literal Markdown as selectable text. For a skill folder, it includes `SKILL.md` and supporting Markdown documents and lists other bundled files. This exports the skill instructions for distribution. The advisor's resulting visual branding PDF uses the [builder inside the skill](skills/advisor-brand-guide/references/pdf-builder.md), which embeds the actual palette, logos, and photos. Check each PDF's extracted text and rendered pages before sharing it.

## Install from GitHub in Codex

Ask Codex:

> Use the skill installer to install `skills/advisor-brand-guide` from `SuperFastTaco/advisor-ai-skills`.

The installer needs the skill-folder path, not just the repository name. Codex normally installs to `~/.codex/skills`; a configured `CODEX_HOME` changes that location. The bundled installer stops if the destination already exists, so updating an installed skill needs a separate replacement step.

Codex installation behavior has been checked against the bundled installer. Native installation in other agents will be documented after verification.

## Sharing a release

A release should contain the completed skill folder, a PDF generated from that version, and clear usage and installation instructions. Record the version in the skill's frontmatter using `metadata.version` and keep the PDF and folder at the same version. The source repository is [SuperFastTaco/advisor-ai-skills](https://github.com/SuperFastTaco/advisor-ai-skills).

Local authoring context belongs in `.local/`, which is excluded from Git. Generated PDFs go in `output/pdf/`, which is also excluded from Git; selected PDFs and customer handouts can be distributed as release attachments.

## License

This library is licensed under the [MIT License](LICENSE), copyright 2026 Kevin Nuber. You may use, modify, and redistribute the skills, including commercially, while preserving the copyright and license notice. The installable skill folder includes its own copy of the license notice.
