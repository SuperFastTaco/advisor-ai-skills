# Advisor AI Skills

A library created by Kevin Nuber to help independent financial advisors and their teams run and grow their practices.

Each skill guides an agent through a specific advisor workflow and produces a usable result, such as a documented process, an ideal-client profile, or a workshop follow-up plan.

## Get started

Choose the workflow you need. Each skill folder contains its instructions and bundled resources; the customer guide explains how to start.

| Skill folder | Result | Customer guide |
|---|---|---|
| [Advisor Brand Guide](skills/advisor-brand-guide/) | Your practice's Markdown branding rules and visual PDF | [Create your brand guide](guides/start-here.md) |
| [First Appointment Packet](skills/first-appointment-packet/) | Six coordinated packet designs, review mockups, and a requested final ordering handoff | [Create your appointment packet](guides/first-appointment-packet-start-here.md) |
| [Advisor Logo Design](skills/advisor-logo-design/) | Practice-specific logo concepts, revisions, and selected logo assets and rules | [Create your logo](guides/advisor-logo-design-start-here.md) |

For downloadable PDF editions and customer handouts, see [the latest release](https://github.com/SuperFastTaco/advisor-ai-skills/releases/latest).

## Advisor Brand Guide

[Advisor Brand Guide](skills/advisor-brand-guide/SKILL.md) first requests and scans the advisor's logos, website, brochures, and photos, then asks only about missing information or conflicts. It creates `Advisor-branding-rules.md` and `Advisor-branding-rules.pdf`, covering mission, values, services, ideal clients, positioning, voice, color palette, typography, logos, imagery, and other marketing rules. The PDF embeds color swatches and available logos and photos. It works without prior AI experience; unavailable materials remain clearly identified.

Customer instructions are in [Start Here](guides/start-here.md). The skill instructions and the advisor's finished brand guide are different documents: the first creates the second.

In Codex, after installation, start with:

> Use $advisor-brand-guide to review my website, logos, brochures, and photos first, ask only missing questions, and create Advisor-branding-rules.md and a visual PDF for my agents.

## First Appointment Packet

[First Appointment Packet](skills/first-appointment-packet/SKILL.md) uses your website, logo assets, and brand guide to design a packet mailed before an already scheduled first appointment. It creates six coordinated pieces: a mailing envelope, pen, notepad, handwritten note card, card envelope, and company brochure. The starting quantity is 50 packets; tell the agent if you need a different count.

It accepts the Advisor Brand Guide's `Advisor-branding-rules.md` output and readable PDF brand guides. The agent reviews your materials, asks only for missing details, prepares the first designs and mockups, and applies your revisions. When you request the final handoff, it assembles the selected files, project preview, editable Word ordering guide, and ZIP, identifying any remaining printer preparation.

Customer instructions are in [Create your appointment packet](guides/first-appointment-packet-start-here.md).

In Codex, after installation, start with:

> Use $first-appointment-packet to review my website, logo files, and brand guide, ask only for missing information, and design all six pieces for 50 first-appointment packets. Show the first pass for review.

## Advisor Logo Design

[Advisor Logo Design](skills/advisor-logo-design/SKILL.md) reviews the advisor's branding guide, website, logos, brochures, and conversation context before asking only unanswered questions. It develops distinct concepts for the practice's audience and positioning, supports revisions, and prepares accepted assets and reusable logo rules. It works with an existing brand guide or a new practice.

Native image generation is preferred when available. The complete folder includes an optional Gemini/OpenAI API helper for capable environments and a prompt-only route when generation is unavailable. Native generation has been checked with fictional materials; API handling has been checked offline, with live paid calls and other agents' installation behavior still unverified.

After installation in Codex, start with:

> Use $advisor-logo-design to review my branding guide, website, logos, and brochures first, ask only unanswered questions, and create three distinct logo concepts for my practice.

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

For Advisor Brand Guide, ask Codex:

> Use the skill installer to install `skills/advisor-brand-guide` from `SuperFastTaco/advisor-ai-skills`.

For First Appointment Packet, ask Codex:

> Use the skill installer to install `skills/first-appointment-packet` from `SuperFastTaco/advisor-ai-skills`.

For Advisor Logo Design, ask Codex:

> Use the skill installer to install `skills/advisor-logo-design` from `SuperFastTaco/advisor-ai-skills`.

The installer needs the skill-folder path, not just the repository name. Codex normally installs to `~/.codex/skills`; a configured `CODEX_HOME` changes that location. The bundled installer stops if the destination already exists, so updating an installed skill needs a separate replacement step.

Codex installation behavior has been checked against the bundled installer. Native installation in other agents will be documented after verification.

## Sharing a release

A release should contain the completed skill folder, a PDF generated from that version, and clear usage and installation instructions. Record the version in the skill's frontmatter using `metadata.version` and keep the PDF and folder at the same version. The source repository is [SuperFastTaco/advisor-ai-skills](https://github.com/SuperFastTaco/advisor-ai-skills).

Local authoring context belongs in `.local/`, which is excluded from Git. Generated PDFs go in `output/pdf/`, which is also excluded from Git; selected PDFs and customer handouts can be distributed as release attachments.

## License

This library is licensed under the [MIT License](LICENSE), copyright 2026 Kevin Nuber. You may use, modify, and redistribute the skills, including commercially, while preserving the copyright and license notice. Each installable skill folder includes its own copy of the license notice.

Advisor Logo Design also retains Duc Nguyen's upstream copyright and MIT notice in its [license and attribution](skills/advisor-logo-design/LICENSE.md).
