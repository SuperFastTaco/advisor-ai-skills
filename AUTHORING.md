# Creating an Advisor Practice Skill

Write a skill that helps an advisor or team member complete a particular task. Start with the advisor's problem and the work they need at the end.

## Define the job

Before drafting, establish:

- Who will use the skill: the advisor, an assistant, an office manager, or a marketing team member.
- The task that should activate it and the result it should produce.
- What information the advisor can reasonably provide.
- Which tools or files are essential, and how to proceed if they are unavailable.
- What a useful finished result looks like.

Use a conversation to resolve missing details that materially affect the result. Do useful work with the information already available, and identify assumptions that affect the output.

## Write the portable source

Use the template in `templates/skill-template.md`. A skill's required entry point is `skills/<skill-name>/SKILL.md`, with YAML frontmatter containing `name` and `description`.

The description tells the agent when the skill applies. The body supplies the workflow, useful decision criteria, and the expected deliverable. Include the domain knowledge that improves the task; avoid generic advice the agent already knows.

Use the advisor's business context as an input. Shared instructions must not require Kevin's Personal Brain, internal customer notes, personal paths, accounts, or preferred tools.

For longer conditional guidance, create a reference inside the same skill folder and link to it with a relative path. Add scripts or assets only when they improve the actual workflow. A short skill may need only `SKILL.md`.

## Make the result useful to an advisor

Favor clear language, concrete examples, and work the advisor can review, use, or hand to their team. Adapt the output to the request rather than forcing every task into the same report format.

Use supplied evidence for business facts, customer quotes, and results. Distinguish proposed changes from the practice's current process. When a workflow involves financial, tax, or product claims, include the source verification and firm-specific guidance appropriate to those claims.

A skill does not grant access to accounts or authorize external actions. Describe required integrations honestly and keep the workflow within the user's request and existing permissions.

## Check the actual behavior

Try a realistic request with representative inputs. Review whether the agent produces a result the intended advisor or team member can use, asks only necessary questions, and handles relevant missing information sensibly.

Use fictional or anonymized examples for anything that will be shared. Keep private test inputs and outputs outside the public skill folder.

For Codex, run the available skill validator as well. Validation catches structural errors; it does not prove that the workflow makes good decisions.

## Produce the two editions

Record a version in the skill's frontmatter under `metadata.version`, then generate the PDF from the completed folder:

```sh
python3 scripts/export_pdf.py skills/<skill-name> --output output/pdf/<skill-name>.pdf
```

The export includes the instruction Markdown and any supporting Markdown documents. It lists other resources so the reader knows when the folder is needed. Scripts, images, spreadsheets, and other non-Markdown files remain in the folder.

Check that text extracts correctly and inspect the rendered pages. A PDF intended for agents must contain actual text rather than screenshots of instructions.

Keep the PDF and folder at the same version. Once the GitHub location is known, include a link to the skill folder in the released instructions.
