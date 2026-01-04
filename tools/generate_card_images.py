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


SCENE_CUES = {
    "forest": "mist-laced ancient forest with towering trees and mossy stones",
    "aquatic": "murky bayou water with cypress roots and bioluminescent mist",
    "water": "misty river delta with reflective shallows and drifting reeds",
    "swamp": "murky bayou water with cypress roots and bioluminescent mist",
    "coast": "rocky shoreline with tidal pools and sea spray at golden hour",
    "ocean": "stormy open sea with towering waves and distant cliffs",
    "urban": "rain-slicked city alley with cracked concrete and neon reflections",
    "ruin": "crumbling stone ruins overgrown with moss and broken statues",
    "machine": "copper-and-iron workshop filled with gears, steam, and sparks",
    "bridge": "high-span bridge shrouded in fog and flickering lantern light",
    "storm": "lightning-slashed sky with swirling clouds and wind-tossed silhouettes",
    "desert": "sun-bleached badlands with eroded rock spires and drifting dust",
    "badlands": "sun-bleached badlands with eroded rock spires and drifting dust",
    "volcanic": "smoldering caldera with rivers of lava and ash-darkened skies",
    "frost": "glacial tundra with drifting snow and jagged ice formations",
    "tundra": "windswept tundra of ice ridges and distant glaciers",
    "mountain": "jagged mountain range with alpine mist and craggy cliffs",
    "sky": "cloud-wreathed sky vista framed by soaring peaks",
    "shrine": "serene shrine with stone lanterns, torii, and hanging prayer tags",
    "library": "ancient library of towering shelves, warm lamplight, and dust motes",
    "cavern": "luminescent cavern with mineral pillars and pools of reflected light",
    "sanctuary": "quiet sanctuary garden with flowing water and protective wards",
    "village": "lantern-lit village square with cobblestone paths and market stalls",
    "wasteland": "bleak wasteland of broken architecture and drifting ash",
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


def _scene_from_card(card: Card) -> str:
    territory_types = getattr(card, "territory_types", []) or []
    search_terms = list(territory_types) + list(card.tags)

    for term in search_terms:
        normalized = term.lower()
        for keyword, description in SCENE_CUES.items():
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

    scene = _scene_from_card(card)
    lore_snippet = _text_snippet(card.text)
    territory_hint = getattr(card, "territory_types", []) or []
    territory_text = ", ".join(territory_hint)

    if card.type == CardType.CRYPTID:
        parts = [
            (
                f"Standalone creature portrait of '{card.name}' in the shared universe, "
                "semi-realistic dark folklore realism, anatomically grounded yet uncanny, "
                "muted earth-tone palette, cinematic lighting tuned to its biome"
            ),
            (
                f"Environment reflects their territory types ({territory_text}) "
                if territory_text
                else "Environment reflects their implied territory "
            )
            + f"with cues from: {scene}.",
            "Atmospheric depth, tangible weathering, and grounded landscape that keeps the creature rooted in its biome.",
            "Full body or three-quarter view of the creature centered in the frame, naturalistic background only.",
        ]
        if lore_snippet:
            parts.append(f"Lore cue from card text: {lore_snippet}.")
        parts.append(
            "Shallow depth of field, subtle horror without gore, highly detailed textures, no text, no symbols, no borders, no card frame."
        )
        return " ".join(parts)

    if card.type == CardType.TERRITORY:
        parts = [
            (
                f"Expansive land illustration for territory '{card.name}', painterly and grounded, "
                "evokes natural terrain and landmarks rather than creatures"
            ),
            (
                "Wide-angle framing that showcases the environment: rolling terrain, skyline, and key landmarks; "
                "reads as a land card and not a character portrait"
            ),
            (
                "Landscape should reflect tags like forest, shrine, desert, water, or urban through flora, architecture, "
                f"and geography. Environment cue: {scene}."
            ),
        ]
        if lore_snippet:
            parts.append(
                f"Mood and environmental storytelling inspired by the card text: {lore_snippet}."
            )
        parts.append(
            "No figures or creatures in focus, no card frame or overlays, cinematic composition with depth."
        )
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
        parts.append("Symbolic props only, no UI elements, no borders, no lettering.")
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
        parts.append("Glowing rim light, no human text, no borders, no card framing.")
        return " ".join(parts)

    return (
        f"Standalone illustration of '{card.name}', cinematic and cohesive art direction. "
        f"Scene suggestion: {scene}. "
        f"No text, no UI, no card frame."
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
