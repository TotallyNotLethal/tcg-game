"""Generate image assets for each card using ChatGPT image generation."""
from __future__ import annotations

import argparse
import base64
import sys
from pathlib import Path
import re
from typing import Iterable, Set

import requests

from openai import APIStatusError, OpenAI, PermissionDeniedError

# Ensure the project root is on the import path when executed as a script
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tcg.cards import (
    Card,
    CardType,
    cryptid_pool,
    event_pool,
    god_pool,
    slugify,
    territory_card_pool,
)


TAG_SCENE_CUES = {
    "forest": "mist-laced ancient forest with towering trees and mossy stones",
    "aquatic": "murky bayou water with cypress roots and bioluminescent mist",
    "urban": "rain-slicked city alley with cracked concrete and neon reflections",
    "storm": "lightning-slashed sky with swirling clouds and wind-tossed silhouettes",
    "desert": "sun-bleached badlands with eroded rock spires and drifting dust",
    "frost": "glacial tundra with drifting snow and jagged ice formations",
}


def iter_unique_cards() -> Iterable[Card]:
    """Yield each unique card across all pools once."""

    pools = [cryptid_pool(), event_pool(), territory_card_pool(), god_pool()]
    seen: Set[str] = set()
    for pool in pools:
        for card in pool.values():
            if card.name in seen:
                continue
            seen.add(card.name)
            yield card


def _scene_from_tags(tags: Iterable[str]) -> str:
    for tag in tags:
        normalized = tag.lower()
        for keyword, description in TAG_SCENE_CUES.items():
            if keyword in normalized:
                return description
    return "moody natural biome that fits the legend"


def _text_snippet(text: str, *, limit: int = 140) -> str:
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    if not cleaned:
        return ""

    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", cleaned) if part.strip()]
    snippet = sentences[0] if sentences else cleaned
    if len(snippet) > limit:
        snippet = snippet[:limit].rstrip()
        if snippet and snippet[-1] not in {".", "!", "?"}:
            snippet += "..."
    return snippet


def build_prompt(card: Card) -> str:
    """Create a descriptive prompt for the image model based on card data."""

    scene = _scene_from_tags(card.tags)
    lore_snippet = _text_snippet(card.text)

    if card.type == CardType.CRYPTID:
        parts = [
            (
                f"Cryptid illustration of '{card.name}' in the shared universe, "
                "semi-realistic dark folklore realism, anatomically grounded yet uncanny, "
                "muted earth-tone palette, cinematic lighting tuned to its biome"
            ),
            f"Scene: {scene} with atmospheric depth and tangible weathering.",
        ]
        if lore_snippet:
            parts.append(f"Lore cue from card text: {lore_snippet}.")
        parts.append("Shallow depth of field, subtle horror without gore, highly detailed textures, no text, no symbols, no borders.")
        return " ".join(parts)

    if card.type == CardType.TERRITORY:
        parts = [
            (
                f"Atmospheric landscape concept art for territory '{card.name}', painterly and grounded, "
                "captures the feel of the battlefield location"
            ),
            f"Environment cue: {scene}.",
        ]
        if lore_snippet:
            parts.append(f"Mood inspired by card text: {lore_snippet}.")
        parts.append("No card frame, no text, cinematic composition.")
        return " ".join(parts)

    if card.type == CardType.EVENT:
        parts = [
            (
                f"Dynamic vignette of the event '{card.name}', energy and motion emphasized, "
                "magical realism style"
            ),
            f"Backdrop hint: {scene}.",
        ]
        if lore_snippet:
            parts.append(f"Effect flavor: {lore_snippet}.")
        parts.append("Symbolic props only, no UI elements or lettering.")
        return " ".join(parts)

    if card.type == CardType.GOD:
        parts = [
            (
                f"Majestic deity portrait for '{card.name}', mythic grandeur with sacred motifs, "
                "semi-realistic painterly render"
            ),
            f"Setting: {scene}.",
        ]
        if lore_snippet:
            parts.append(f"Divine aspect hint: {lore_snippet}.")
        parts.append("Glowing rim light, no human text, no card borders.")
        return " ".join(parts)

    return (
        f"Illustration for card '{card.name}', cinematic and cohesive art direction. "
        f"Scene suggestion: {scene}. "
        f"No text or UI elements."
    )


def generate_image(
    card: Card,
    output_dir: Path,
    client: OpenAI,
    *,
    overwrite: bool = False,
    size: str = "1024x1024",
    model: str = "dall-e-3",
) -> Path:
    """Call ChatGPT image generation for a card and persist it to disk."""

    output_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(card.name)
    output_path = output_dir / f"{slug}.png"
    if output_path.exists() and not overwrite:
        print(f"Skipping {card.name}: {output_path} already exists")
        return output_path

    prompt = build_prompt(card)
    try:
        response = client.images.generate(
            model=model,
            prompt=prompt,
            size=size,
        )
    except PermissionDeniedError as exc:  # pragma: no cover - API behavior
        message = (
            "Image generation failed with a permission error. The selected model "
            f"'{model}' may require organization verification or access. Try choosing "
            "a model available to your account (e.g., 'dall-e-3') or verify your "
            "organization at https://platform.openai.com/settings/organization/general."
        )
        raise SystemExit(message) from exc
    except APIStatusError as exc:  # pragma: no cover - API behavior
        raise SystemExit(f"Image generation failed: for {prompt} {exc.message}") from exc

    image = response.data[0]
    image_b64 = getattr(image, "b64_json", None)
    if image_b64:
        output_path.write_bytes(base64.b64decode(image_b64))
    elif getattr(image, "url", None):  # pragma: no cover - depends on API response
        download = requests.get(image.url, timeout=30)
        download.raise_for_status()
        output_path.write_bytes(download.content)
    else:  # pragma: no cover - depends on API response
        raise SystemExit(
            "Image generation did not return image data. "
            "Try rerunning with a supported model (e.g., 'dall-e-3')."
        )

    print(f"Saved {card.name} -> {output_path}")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate image assets for all cards.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("assets/cards"),
        help="Directory to save generated images (default: assets/cards)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Recreate images even if a file already exists",
    )
    parser.add_argument(
        "--size",
        default="1024x1024",
        choices=["1024x1024", "1024x1536", "1536x1024", "auto"],
        help="Image size to request from the API (default: 1024x1024)",
    )
    parser.add_argument(
        "--model",
        default="dall-e-3",
        help=(
            "Image generation model to use (e.g., gpt-image-1 or dall-e-3). "
            "Use a model available to your account."
        ),
    )
    args = parser.parse_args()

    client = OpenAI()
    for card in iter_unique_cards():
        generate_image(
            card,
            args.output_dir,
            client,
            overwrite=args.overwrite,
            size=args.size,
            model=args.model,
        )


if __name__ == "__main__":
    main()
