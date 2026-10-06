# Image Generation and Prompt Guidance

Use the same approved brief with whichever generation route is available. Do not make image tools or API setup the advisor's first task.

## Native route

Prefer the host's actual image-generation tool. In Codex use the built-in image tool, following its current schema and installed image-generation guidance. Inspect local input images before attaching them. Label each reference as an existing logo, selected edit target, or visual inspiration. Use the tool's reference mechanism rather than claiming a file was submitted by mentioning its path in the prompt.

Request plain white or neutral comparison backgrounds for first concepts. Request transparent output for applicable final assets and inspect the alpha channel. Preserve existing transparency during edits. Save project assets in the chosen project folder and keep originals.

Generate the requested distinct concepts separately unless the user requested a single comparison board. A comparison board is a review artifact, not a substitute for individually usable final logos. Use targeted edits with an actual selected reference when refining.

## API route: optional and explicit

Use the bundled scripts/generate_image.py only when the advisor has selected API generation, the environment can run Python 3.10+, and outbound provider access is available. It uses Python's standard library; no third-party package or other skill is required. It handles new images and supplied image references, writes the actual returned format, and refuses to overwrite files.

The helper requires an explicit provider and model. Confirm the intended number of images/iterations and the customer's chosen paid route; reuse authorization for that scope. Do not silently switch providers, charge an API account after a native-tool failure, or perform unlimited retries. Each run requests one image. There are no automatic retries.

Keys belong in the customer's environment: OPENAI_API_KEY or GEMINI_API_KEY. Never ask them to paste a key in chat, embed a key in a prompt, store one in the skill, or publish credentials. Do not print environment values. API billing is separate from a ChatGPT/Codex subscription.

Resolve the installed skill folder from the loaded SKILL.md location; use it as SKILL_DIR. Do not assume the author's local paths. In these commands, replace MODEL_ID with the chosen currently available image model; it is not a real model ID:

    python3 "$SKILL_DIR/scripts/generate_image.py" --provider openai --model MODEL_ID --prompt-file "./prompts/concept-1.txt" --output "./brand-assets/logos/concept-1.png" --dry-run

Remove --dry-run only for the agreed live request. For a referenced refresh or revision:

    python3 "$SKILL_DIR/scripts/generate_image.py" --provider gemini --model MODEL_ID --prompt-file "./prompts/refinement.txt" --reference "./brand-assets/logos/selected.png" --output "./brand-assets/logos/refined.png"

The helper sends local image references as inline data. Use --reference repeatedly for multiple inputs. It supports PNG, JPEG, and WebP inputs. OpenAI output options include --background transparent|opaque|auto, --size, and --quality for models that support those settings. Gemini uses --aspect-ratio when supplied; request any background preference in the prompt and verify the result rather than assuming alpha support.

--dry-run validates inputs and displays a request summary without a key, network call, output image, or image data. API errors stop with a short status message. Do not claim success when a provider returns no image. Confirm quota/account/model access with the customer before trying another paid request.

## Other hosts and prompt-only route

Claude Code can run a helper subject to its local permissions and network access. Claude chat capabilities vary. Claude API skill containers have no external network access; an application must provide an external image-generation tool. An attached PDF does not supply credentials or make an API executable.

If no generation route is available, deliver the completed brief, three distinct ready-to-use prompts, intended settings, and a list of reference files and their roles. Give a simple instruction to run a prompt in an image tool and bring the result back. Then inspect the returned result and support refinement. Describe this honestly as a prompt package; do not insert fabricated outputs or silently substitute schematic artwork for promised generated images.

## Portable prompt structure

Write a concise, explicit prompt for each direction:

    Purpose: Logo concept for [exact practice name], serving [documented ideal clients].
    Positioning: [actual service focus and supported distinction].
    Direction: [one specific structure, symbolism, typography, and intended feeling].
    Palette: [confirmed colors, or explicitly proposed palette].
    Text, verbatim: "[exact name]" [optional approved tagline].
    References: [numbered image roles and elements to retain, if actually attached].
    Composition: One flat, clean logo on a plain background; balanced spacing.
    Constraints: Simple silhouette, readable name, useful one-color form; [brief-specific exclusions].

For a symbol-only exploration explicitly request no lettering. For a wordmark, quote the exact name and inspect every character afterward. For a revision state "Change [specific element]. Preserve [specific selected identity elements]." Keep confirmed spelling and required wording fixed across prompts.

"Vector-style" describes appearance, not file structure. Never promise SVG, editable type, printer acceptance, or legal clearance based on a generated raster image.

## Provider references and verification

Documentation checked October 6, 2026. Recheck model availability and current options when configuring a live provider; do not treat example model names in another skill as permanent defaults.

- [OpenAI image generations](https://developers.openai.com/api/reference/resources/images/methods/generate)
- [OpenAI image references/edits](https://developers.openai.com/api/reference/resources/images/methods/edit)
- [Gemini generateContent schema](https://ai.google.dev/api/generate-content)
- [Gemini image-generation capabilities](https://ai.google.dev/gemini-api/docs/image-generation)
- [Claude skill runtime constraints](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [Codex image-generation use](https://learn.chatgpt.com/docs/image-generation)

Native generation and the prompt workflow are the primary routes. The API helper's request/response handling is checked offline; paid provider calls and native installation in other agents have not been verified. Do not describe those routes as live-tested or document unsupported installation behavior.
