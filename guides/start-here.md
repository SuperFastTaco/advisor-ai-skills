# Create Your Practice's Brand Guide

This skill creates a branding reference your AI agents can use when making marketing materials. Start with what your company already uses: its website, logos, brochures, photos, and any existing brand rules.

## Start the conversation

If the skill is installed in Codex, use:

> Use $advisor-brand-guide to create my practice's branding rules. Review my website, logos, brochures, and photos first, then ask only about what is missing. Create Advisor-branding-rules.md and a visual PDF for my agents.

If you are using the skill's PDF, attach it to an agent that can read PDFs and use:

> Read the attached Advisor Brand Guide skill and follow it to create my practice's branding rules. Ask for my website, logos, brochures, and photos, review them first, then ask only missing questions. Create both the Markdown rules and visual PDF.

Share your website link and attach the materials you have. Include logo versions, company brochures, headshots, team or office photos, and any existing brand guide. It is fine if some do not exist yet.

The agent reviews the supplied materials before asking about missing information or conflicting choices. The skill includes a bank of 14 follow-up questions; the agent skips answered questions and asks only one to three at a time. It then creates the guide. Review the draft and tell the agent what to change.

## Save the guide it creates

The skill instructions and your completed brand guide are two different files. The skill helps the agent create the guide. Your finished guide describes your own practice and is the file to reuse for future work.

Save both `Advisor-branding-rules.md` and `Advisor-branding-rules.pdf`. The PDF includes your color palette, logos, photos, mission, values, services, ideal client, and guidance for creating future marketing. Keep the companion `brand-assets/` folder with them so an agent can use the original logo and photo files.

## Use it for your next task

Attach your completed guide in a future chat and write:

> Use the attached Advisor-branding-rules to create a welcome email for a new client. Follow my practice's voice and use only the facts in the rules or this conversation.

You can also add the guide to a project or agent knowledge area if your tool supports that. Attaching a file once does not guarantee the agent will remember it in every future chat.

For design work, provide the original logo or photo files the agent needs as well. Update the rules as your practice changes; ask the agent to revise both files together.
