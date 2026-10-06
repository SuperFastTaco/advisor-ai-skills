#!/usr/bin/env python3
"""Optional, explicit single-image API route. Python 3.10+, standard library only."""

from __future__ import annotations

import argparse
import base64
import binascii
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request


class GenerationError(Exception):
    """An actionable error without credentials or raw provider response data."""


FORMATS = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp"}


def image_mime(data: bytes) -> str:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    raise GenerationError("Image data is not PNG, JPEG, or WebP.")


def encode_reference(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise GenerationError("A reference file does not exist.")
    if path.stat().st_size > 20 * 1024 * 1024:
        raise GenerationError("Each reference must be at most 20 MiB.")
    data = path.read_bytes()
    return {"mime": image_mime(data), "data": base64.b64encode(data).decode("ascii")}


def build_request(args: argparse.Namespace, prompt: str) -> tuple[str, dict]:
    if not re.fullmatch(r"[A-Za-z0-9._-]+", args.model):
        raise GenerationError("Use a model ID without slashes, spaces, or URL components.")
    if len(args.reference) > 8:
        raise GenerationError("Use at most eight reference images per request.")
    references = [encode_reference(path) for path in args.reference]
    if args.provider == "openai":
        if args.aspect_ratio:
            raise GenerationError("For OpenAI use --size; --aspect-ratio is for Gemini.")
        payload = {"model": args.model, "prompt": prompt, "n": 1, "output_format": "png"}
        for name in ("background", "size", "quality"):
            value = getattr(args, name)
            if value is not None:
                payload[name] = value
        method = "generations"
        if references:
            method = "edits"
            payload["images"] = [
                {"image_url": "data:" + ref["mime"] + ";base64," + ref["data"]}
                for ref in references
            ]
        return "https://api.openai.com/v1/images/" + method, payload
    if any(getattr(args, name) is not None for name in ("background", "size", "quality")):
        raise GenerationError("Gemini uses the prompt for background and --aspect-ratio for shape.")
    parts = [
        {"inlineData": {"mimeType": ref["mime"], "data": ref["data"]}}
        for ref in references
    ]
    parts.append({"text": prompt})
    config = {"responseModalities": ["TEXT", "IMAGE"]}
    if args.aspect_ratio:
        if not re.fullmatch(r"\d{1,2}:\d{1,2}", args.aspect_ratio):
            raise GenerationError("Aspect ratio must look like 1:1 or 16:9.")
        config["imageConfig"] = {"aspectRatio": args.aspect_ratio}
    payload = {"contents": [{"role": "user", "parts": parts}], "generationConfig": config}
    return "https://generativelanguage.googleapis.com/v1beta/models/" + args.model + ":generateContent", payload


def call_provider(url: str, payload: dict, provider: str, timeout: int) -> dict:
    variable = "OPENAI_API_KEY" if provider == "openai" else "GEMINI_API_KEY"
    key = os.environ.get(variable)
    if not key:
        raise GenerationError("Set " + variable + " locally before a live request; never paste it in chat.")
    headers = {"Content-Type": "application/json"}
    if provider == "openai":
        headers["Authorization"] = "Bearer " + key
    else:
        headers["x-goog-api-key"] = key
    request = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(80 * 1024 * 1024 + 1)
    except urllib.error.HTTPError as exc:
        messages = {
            400: "Check the model, options, prompt, and reference requirements.",
            401: "Check the locally configured API key.",
            403: "Check account permissions and model access.",
            404: "Check model availability.",
            429: "Check quota or rate limits before another request.",
        }
        raise GenerationError("Provider HTTP " + str(exc.code) + ". " +
                              messages.get(exc.code, "Check provider status before another request.") +
                              " No automatic retry was made.") from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise GenerationError("Network request failed or timed out. Check access before retrying; a timed-out request may still be billed.") from None
    if len(raw) > 80 * 1024 * 1024:
        raise GenerationError("Provider response exceeds the 80 MiB limit.")
    try:
        result = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        raise GenerationError("Provider returned an unreadable response.") from None
    if not isinstance(result, dict):
        raise GenerationError("Provider returned an unexpected response.")
    return result


def extract_image(response: dict, provider: str) -> tuple[bytes, str]:
    encoded = None
    stated_mime = None
    if provider == "openai":
        for item in response.get("data") or []:
            if isinstance(item, dict) and item.get("b64_json"):
                encoded = item["b64_json"]
                break
    else:
        for candidate in response.get("candidates") or []:
            for part in candidate.get("content", {}).get("parts") or []:
                inline = part.get("inlineData") or part.get("inline_data") or {}
                mime = inline.get("mimeType") or inline.get("mime_type") or ""
                if mime.startswith("image/") and inline.get("data"):
                    encoded, stated_mime = inline["data"], mime
                    break
            if encoded:
                break
    if not isinstance(encoded, str) or not encoded:
        raise GenerationError("Provider returned no image. Check request/account support; no file was saved.")
    try:
        data = base64.b64decode(encoded, validate=True)
    except (ValueError, binascii.Error):
        raise GenerationError("Provider returned invalid image encoding.") from None
    mime = image_mime(data)
    if stated_mime and stated_mime != mime:
        raise GenerationError("Provider image type does not match its data.")
    return data, mime


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", required=True, choices=("openai", "gemini"))
    parser.add_argument("--model", required=True, help="Explicit, available image model ID.")
    parser.add_argument("--prompt-file", required=True, type=Path)
    parser.add_argument("--reference", action="append", default=[], type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--background", choices=("transparent", "opaque", "auto"))
    parser.add_argument("--size")
    parser.add_argument("--quality", choices=("low", "medium", "high", "auto", "xhigh", "max"))
    parser.add_argument("--aspect-ratio")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        if not 1 <= args.timeout <= 600:
            raise GenerationError("Timeout must be between 1 and 600 seconds.")
        prompt = args.prompt_file.read_text(encoding="utf-8").strip()
        if not prompt or len(prompt) > 32000:
            raise GenerationError("Prompt must contain 1 to 32000 characters.")
        if args.output.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
            raise GenerationError("Output must end in .png, .jpg, .jpeg, or .webp.")
        metadata_path = args.output.with_suffix(".generation.json")
        possible = [args.output, metadata_path] + [args.output.with_suffix(ext) for ext in FORMATS.values()]
        if any(path.exists() for path in possible):
            raise GenerationError("Output or metadata already exists; choose a new filename.")
        url, payload = build_request(args, prompt)
        summary = {
            "status": "dry-run" if args.dry_run else "requested",
            "provider": args.provider, "model": args.model,
            "reference_count": len(args.reference),
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        }
        if args.dry_run:
            print(json.dumps(summary, indent=2))
            return 0
        data, mime = extract_image(call_provider(url, payload, args.provider, args.timeout), args.provider)
        actual_output = args.output.with_suffix(FORMATS[mime])
        actual_output.parent.mkdir(parents=True, exist_ok=True)
        with actual_output.open("xb") as output:
            output.write(data)
        summary.update({
            "status": "generated-raster", "output": str(actual_output),
            "mime_type": mime, "image_sha256": hashlib.sha256(data).hexdigest(),
            "created_utc": datetime.now(timezone.utc).isoformat(),
        })
        try:
            with metadata_path.open("x", encoding="utf-8") as metadata:
                json.dump(summary, metadata, indent=2)
        except OSError:
            print("Image saved, but generation metadata could not be written.", file=sys.stderr)
        print(json.dumps(summary, indent=2))
        return 0
    except (GenerationError, OSError, UnicodeDecodeError) as exc:
        if isinstance(exc, GenerationError):
            message = str(exc)
        else:
            message = "A local input or output file could not be read or written."
        print("error: " + message, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
