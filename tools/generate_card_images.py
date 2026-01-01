"""Generate image assets for each card using ChatGPT image generation."""
from __future__ import annotations

import argparse
import base64
from pathlib import Path
from typing import Iterable, Set

from openai import OpenAI

from tcg.cards import Card, cryptid_pool, event_pool, god_pool, slugify, territory_card_pool


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


def build_prompt(card: Card) -> str:
    """Create a descriptive prompt for the image model based on card data."""

    parts = [f"Illustration for a trading card named '{card.name}'."]
    parts.append(f"Card type: {card.type.name.title()}.")
    if card.tags:
        parts.append(f"Style cues/tags: {', '.join(card.tags)}.")
    if card.text:
        parts.append(f"Card rules text: {card.text}")
    return " ".join(parts)


def generate_image(card: Card, output_dir: Path, client: OpenAI, overwrite: bool = False) -> Path:
    """Call ChatGPT image generation for a card and persist it to disk."""

    output_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(card.name)
    output_path = output_dir / f"{slug}.png"
    if output_path.exists() and not overwrite:
        print(f"Skipping {card.name}: {output_path} already exists")
        return output_path

    prompt = build_prompt(card)
    response = client.images.generate(model="gpt-image-1", prompt=prompt, size="512x512")
    image_b64 = response.data[0].b64_json
    output_path.write_bytes(base64.b64decode(image_b64))
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
    args = parser.parse_args()

    client = OpenAI()
    for card in iter_unique_cards():
        generate_image(card, args.output_dir, client, overwrite=args.overwrite)


if __name__ == "__main__":
    main()
