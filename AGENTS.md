# Working on this library

Build reusable skills for independent financial advisors and their teams. Each skill should solve a specific practice problem and produce a usable result.

- Read `README.md` and `AUTHORING.md` before creating or revising a skill.
- When available, read `.local/authoring-context.md` for Kevin's business context and Personal Brain source links. This private file is not part of the customer package.
- Author skills in `skills/<skill-name>/SKILL.md`, using lowercase names with hyphens. Use `templates/skill-template.md` as a starting point, removing all template guidance before release.
- Keep instructions and required resources inside each skill folder. Use relative links. Customers must not need Kevin's vault, local paths, credentials, or personal tool configuration.
- Make the Markdown folder the source of truth. Regenerate the PDF after changing instructions or supporting references.
- Keep customer records, private examples, source captures, and local configuration in `.local/` or outside this repository. Use fictional or anonymized examples in shared files.
- Verify each completed skill with a realistic advisor request. Check the resulting work, not just formatting or headings.
- Document installation only for agents whose behavior has been verified. A readable PDF does not establish native skill installation.
