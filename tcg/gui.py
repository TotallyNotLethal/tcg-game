"""Tkinter GUI for a lightweight hands-on card demo."""
from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

import ttkbootstrap as tb
from PIL import Image, ImageTk

from .cards import Card, Cryptid, EventCard, GodCard, TerritoryCard
from .game import GameState, initial_game


@dataclass
class DragState:
    player_index: Optional[int] = None
    tag: Optional[str] = None
    last_x: int = 0
    last_y: int = 0
    hovered_target: Optional[int] = None


class GameGUI:
    BG_COLOR = "#0d0a11"
    TABLE_COLOR = "#1b1118"
    PANEL_COLOR = "#221723"
    SURFACE_COLOR = "#2d1f2f"
    HAND_COLOR = "#1a121d"
    TEXT_COLOR = "#f4efe5"
    MUTED_TEXT = "#c3b7c5"
    BORDER_COLOR = "#3b2a3c"
    ACCENT_COLOR = "#d1a95a"
    SECONDARY_ACCENT = "#7ec6ff"
    ALERT_COLOR = "#ff8c8c"
    SHADOW_COLOR = "#0a060a"
    CARD_FACE = "#2a1b28"
    CARD_INNER = "#160e17"
    CARD_TYPE_STRIP = "#312b39"
    FIELD_GLOW = "#3fc3a3"
    FACTION_BANNER = "#3d4b6a"

    def __init__(self, deck_template: str = "balanced") -> None:
        self.style = tb.Style(theme="cyborg")
        self.root = self.style.master
        self.root.title("Cryptid TCG Prototype")
        self.root.configure(bg=self.BG_COLOR)
        self.root.option_add("*Font", "Arial 10")
        self.game: GameState = initial_game(deck_template)
        self.cpu_index: int = 0
        self.human_index: int = 1
        self.active_index: int = self.human_index
        self.drag_state: DragState = DragState()
        self.card_tags: Dict[tuple[int, str], Card] = {}
        self.selected_card: Optional[Card] = None
        self.selected_player_idx: Optional[int] = None
        self.selected_tag: Optional[str] = None
        self.drag_overlay: Optional[tk.Toplevel] = None
        self.drag_overlay_canvas: Optional[tk.Canvas] = None
        self.drag_overlay_bounds: Optional[tuple[int, int, int, int]] = None
        self.drag_overlay_card: Optional[Card] = None
        self.detail_window: Optional[tk.Toplevel] = None
        self._detail_focusable: list[tk.Widget] = []
        self.drop_zone_boxes: Dict[int, tuple[int, int, int, int]] = {}
        self.drop_zone_items: Dict[int, tuple[int, int]] = {}
        self.drop_zone_screen_bounds: Dict[int, tuple[int, int, int, int]] = {}
        self.drop_zone_gradient_items: Dict[int, list[int]] = {}
        self.drop_zone_glow_items: Dict[int, list[int]] = {}
        self.drop_zone_tooltips: Dict[int, tuple[int, int]] = {}
        self.drop_zone_slot_items: Dict[int, list[int]] = {}
        self.drop_zone_background_items: Dict[int, int] = {}
        self._playmat_image_cache: Dict[Tuple[str, int, int], tk.PhotoImage] = {}
        self._image_cache: Dict[Tuple[str, int, int], tk.PhotoImage] = {}
        self._font_cache: Dict[Tuple[str, int, str], tkfont.Font] = {}
        self._hovered_hand_tag: Optional[str] = None

        self._build_layout()
        self._render_all()

    def _build_layout(self) -> None:
        banner = tk.Frame(
            self.root,
            bg=self.PANEL_COLOR,
            highlightbackground=self.ACCENT_COLOR,
            highlightthickness=1,
            padx=14,
            pady=10,
        )
        banner.pack(side=tk.TOP, fill=tk.X, padx=12, pady=(12, 8))
        tk.Label(
            banner,
            text="CRYPTID RITES",
            bg=self.PANEL_COLOR,
            fg=self.ACCENT_COLOR,
            font=("Cinzel", 16, "bold"),
        ).pack(anchor="w")
        tk.Label(
            banner,
            text="Drag sigils and beasts onto the ritual field. Stack resolves in style.",
            bg=self.PANEL_COLOR,
            fg=self.MUTED_TEXT,
            font=("Arial", 10),
        ).pack(anchor="w", pady=(2, 0))

        control_frame = tk.Frame(self.root, bg=self.BG_COLOR)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=12, pady=(0, 8))

        self.active_label = tk.Label(
            control_frame,
            text="Active player: You",
            font=("Arial", 12, "bold"),
            bg=self.BG_COLOR,
            fg=self.TEXT_COLOR,
        )
        self.active_label.pack(side=tk.LEFT, padx=(4, 10))

        def make_button(label: str, command: callable) -> tk.Button:
            return tk.Button(
                control_frame,
                text=label,
                command=command,
                bg=self.SURFACE_COLOR,
                fg=self.TEXT_COLOR,
                activebackground=self.ACCENT_COLOR,
                activeforeground=self.BG_COLOR,
                relief=tk.FLAT,
                bd=0,
                padx=12,
                pady=6,
                highlightbackground=self.ACCENT_COLOR,
                highlightthickness=2,
                font=("Arial", 10, "bold"),
            )

        for label, cmd in [
            ("Draw Card", self.draw_card),
            ("Play Selected", self.play_selected),
            ("Play Queued Territory", self.play_queued_territory),
            ("Pray with Gods", self.pray),
            ("Resolve Stack", self.resolve_stack),
            ("End Turn", self.end_turn),
        ]:
            make_button(label, cmd).pack(side=tk.LEFT, padx=4)

        board_frame = tk.Frame(self.root, bg=self.TABLE_COLOR)
        board_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=6)

        # CPU (index 0) on top, human (index 1) on bottom for clarity
        self.player_frames = []
        self.resource_labels = []
        self.influence_labels = []
        self.battlefield_canvases = []
        self.battlefield_layouts: list[dict[str, object]] = []
        self.hand_canvases = []

        for idx, player in enumerate(self.game.players):
            frame = tk.Frame(
                board_frame,
                bg=self.PANEL_COLOR,
                highlightbackground=self.ACCENT_COLOR,
                highlightthickness=1,
                padx=10,
                pady=8,
            )
            frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=8)
            self.player_frames.append(frame)

            header = tk.Frame(frame, bg=self.SURFACE_COLOR, padx=8, pady=6)
            header.pack(side=tk.TOP, fill=tk.X)
            tk.Label(
                header,
                text=player.name,
                bg=self.SURFACE_COLOR,
                fg=self.TEXT_COLOR,
                font=("Arial", 12, "bold"),
            ).pack(side=tk.LEFT)

            info_frame = tk.Frame(frame, bg=self.PANEL_COLOR)
            info_frame.pack(side=tk.TOP, fill=tk.X, pady=4)
            resource_lbl = tk.Label(
                info_frame,
                text="Resources",
                bg=self.PANEL_COLOR,
                fg=self.MUTED_TEXT,
                font=("Arial", 10, "bold"),
            )
            resource_lbl.pack(side=tk.LEFT, padx=4)
            self.resource_labels.append(resource_lbl)

            influence_lbl = tk.Label(
                info_frame,
                text="Influence: 20",
                bg=self.PANEL_COLOR,
                fg=self.TEXT_COLOR,
                font=("Arial", 10, "bold"),
            )
            influence_lbl.pack(side=tk.LEFT, padx=4)
            self.influence_labels.append(influence_lbl)

            battlefield = tk.Canvas(
                frame,
                height=340,
                bg=self.SURFACE_COLOR,
                highlightthickness=1,
                highlightbackground=self.BORDER_COLOR,
            )
            battlefield.pack(side=tk.TOP, fill=tk.X, padx=4, pady=(8, 6))
            self.battlefield_canvases.append(battlefield)
            self.battlefield_layouts.append({})

            hand = tk.Canvas(
                frame,
                height=230,
                bg=self.HAND_COLOR,
                highlightthickness=1,
                highlightbackground=self.BORDER_COLOR,
            )
            hand.pack(side=tk.TOP, fill=tk.X, padx=4, pady=(0, 4))
            self.hand_canvases.append(hand)

        log_frame = tk.Frame(
            self.root,
            bg=self.PANEL_COLOR,
            highlightbackground=self.ACCENT_COLOR,
            highlightthickness=1,
            padx=10,
            pady=8,
        )
        log_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, padx=10, pady=10)
        tk.Label(
            log_frame,
            text="Action Log",
            bg=self.PANEL_COLOR,
            fg=self.MUTED_TEXT,
            font=("Arial", 10, "bold"),
        ).pack(anchor="w")
        self.log_widget = tk.Text(
            log_frame,
            height=12,
            state=tk.DISABLED,
            bg=self.BG_COLOR,
            fg=self.TEXT_COLOR,
            insertbackground=self.ACCENT_COLOR,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=self.BORDER_COLOR,
        )
        self.log_widget.pack(fill=tk.BOTH, expand=True, padx=2, pady=(4, 0))

    def _render_all(self) -> None:
        for idx in range(len(self.game.players)):
            self._render_player(idx)
        self._log(f"{self.game.players[self.active_index].name}'s turn begins.")
        self._update_active_label()

    def _render_player(self, idx: int) -> None:
        player = self.game.players[idx]
        self.resource_labels[idx].configure(text=player.resources.describe())
        self.influence_labels[idx].configure(text=f"Influence: {player.influence}")
        self._render_battlefield(idx)
        self._render_hand(idx)
        self._update_active_label()

    def _render_battlefield(self, idx: int) -> None:
        canvas = self.battlefield_canvases[idx]
        canvas.delete("all")
        player = self.game.players[idx]
        layout = self._get_battlefield_layout(idx)
        self._draw_battlefield_zones(canvas, layout, player)
        self._draw_drop_zone(idx, layout)

        active_card: Optional[Card] = None
        bench_cards: list[Card] = []
        territory_cards: list[object] = []
        prayer_cards: list[Card] = []

        for card in player.battlefield:
            if isinstance(card, TerritoryCard):
                territory_cards.append(card)
            elif isinstance(card, GodCard):
                prayer_cards.append(card)
            elif isinstance(card, Cryptid):
                if not active_card:
                    active_card = card
                else:
                    bench_cards.append(card)
            else:
                bench_cards.append(card)

        for territory in player.territories:
            territory_cards.append(territory)

        if active_card:
            x1, y1, x2, y2 = layout["active"]
            self._draw_card_at(canvas, active_card, x1, y1, x2 - x1, y2 - y1, f"bf_{idx}_active")

        for slot, card in zip(layout["bench"], bench_cards):
            x1, y1, x2, y2 = slot
            self._draw_card_at(canvas, card, x1, y1, x2 - x1, y2 - y1, f"bf_{idx}_bench")

        for i, card in enumerate(prayer_cards):
            x1, y1, x2, y2 = layout["prayer"]
            offset = i * 14
            self._draw_card_at(
                canvas,
                card,
                x1 + offset,
                y1 + offset,
                x2 - x1 - offset * 2,
                y2 - y1 - offset * 2,
                f"bf_{idx}_prayer_{i}",
            )

        for slot, territory in zip(layout["territories"], territory_cards):
            x1, y1, x2, y2 = slot
            self._draw_territory_tile(canvas, territory, x1, y1, x2 - x1, y2 - y1)

    def _get_battlefield_layout(self, idx: int) -> dict[str, object]:
        canvas = self.battlefield_canvases[idx]
        canvas.update_idletasks()
        width = max(canvas.winfo_width(), 820)
        height = max(canvas.winfo_height(), 320)
        padding = 14
        pile_gap = 12
        pile_width, pile_height = 120, 58
        top_y = padding
        piles_total_width = pile_width * 3 + pile_gap * 2
        piles_start_x = max(padding, (width - piles_total_width) / 2)

        center_x = width / 2
        active_width, active_height = 135, 150
        active_y = top_y + pile_height + 14
        bench_spacing = active_width + 16

        territory_width, territory_height = 118, 72
        territory_spacing = territory_width + 18
        territory_y = active_y + active_height + 18

        layout = {
            "deck": (
                piles_start_x,
                top_y,
                piles_start_x + pile_width,
                top_y + pile_height,
            ),
            "discard": (
                piles_start_x + pile_width + pile_gap,
                top_y,
                piles_start_x + pile_width * 2 + pile_gap,
                top_y + pile_height,
            ),
            "prayer": (
                piles_start_x + (pile_width + pile_gap) * 2,
                top_y,
                piles_start_x + pile_width * 3 + pile_gap * 2,
                top_y + pile_height,
            ),
            "active": (
                center_x - active_width / 2,
                active_y,
                center_x + active_width / 2,
                active_y + active_height,
            ),
            "bench": [
                (
                    center_x - 1.5 * bench_spacing,
                    active_y,
                    center_x - 1.5 * bench_spacing + active_width,
                    active_y + active_height,
                ),
                (
                    center_x - 0.5 * bench_spacing,
                    active_y,
                    center_x - 0.5 * bench_spacing + active_width,
                    active_y + active_height,
                ),
                (
                    center_x + 0.5 * bench_spacing,
                    active_y,
                    center_x + 0.5 * bench_spacing + active_width,
                    active_y + active_height,
                ),
                (
                    center_x + 1.5 * bench_spacing,
                    active_y,
                    center_x + 1.5 * bench_spacing + active_width,
                    active_y + active_height,
                ),
            ],
            "territories": [
                (
                    center_x - territory_spacing,
                    territory_y,
                    center_x - territory_spacing + territory_width,
                    territory_y + territory_height,
                ),
                (
                    center_x - territory_width / 2,
                    territory_y,
                    center_x + territory_width / 2,
                    territory_y + territory_height,
                ),
                (
                    center_x + territory_spacing - territory_width,
                    territory_y,
                    center_x + territory_spacing,
                    territory_y + territory_height,
                ),
            ],
        }
        self.battlefield_layouts[idx] = layout
        return layout

    def _draw_battlefield_zones(self, canvas: tk.Canvas, layout: dict[str, object], player: "PlayerState") -> None:
        def draw_slot(coords: tuple[float, float, float, float], label: str, fill: str, accent: str) -> None:
            x1, y1, x2, y2 = coords
            canvas.create_rectangle(x1, y1, x2, y2, outline=accent, width=2, fill=fill)
            canvas.create_text(
                (x1 + x2) / 2,
                y1 - 10,
                text=label,
                fill=self.MUTED_TEXT,
                font=("Arial", 9, "bold"),
            )

        canvas.create_rectangle(0, 0, canvas.winfo_width(), canvas.winfo_height(), fill=self.SURFACE_COLOR, outline="")
        draw_slot(layout["deck"], f"Deck ({len(player.deck)})", self.TABLE_COLOR, self.BORDER_COLOR)
        discard_size = len(getattr(player, "discard_pile", []))
        draw_slot(layout["discard"], f"Discard ({discard_size})", self.TABLE_COLOR, self.BORDER_COLOR)
        draw_slot(layout["prayer"], "Prayer Pile", self.TABLE_COLOR, self.ACCENT_COLOR)

        draw_slot(layout["active"], "Active Slot", self.PANEL_COLOR, self.ACCENT_COLOR)
        for i, bench_slot in enumerate(layout["bench"]):
            draw_slot(bench_slot, f"Ally {i + 1}", self.PANEL_COLOR, self.BORDER_COLOR)

        for i, territory_slot in enumerate(layout["territories"]):
            draw_slot(territory_slot, f"Territory {i + 1}", self.TABLE_COLOR, self.BORDER_COLOR)

        canvas.create_line(
            10,
            layout["territories"][0][1] - 6,
            canvas.winfo_width() - 10,
            layout["territories"][0][1] - 6,
            fill=self.BORDER_COLOR,
            dash=(4, 4),
        )

    def _draw_card_at(
        self, canvas: tk.Canvas, card: Card, x: float, y: float, width: float, height: float, tag: str
    ) -> None:
        shadow = canvas.create_rectangle(
            x + 6,
            y + 8,
            x + width + 6,
            y + height + 8,
            fill=self.SHADOW_COLOR,
            outline="",
        )
        rect = canvas.create_rectangle(
            x,
            y,
            x + width,
            y + height,
            fill=self.CARD_FACE,
            outline=self.ACCENT_COLOR,
            width=2,
        )
        canvas.create_rectangle(
            x + 5,
            y + 5,
            x + width - 5,
            y + height - 5,
            fill=self.CARD_INNER,
            outline=self.BORDER_COLOR,
            width=1,
        )
        canvas.create_rectangle(
            x + 8,
            y + 8,
            x + width - 8,
            y + 30,
            fill=self.CARD_TYPE_STRIP,
            outline=self.ACCENT_COLOR,
            width=1,
        )
        canvas.create_text(
            x + 12,
            y + 19,
            anchor="w",
            text=card.name,
            font=("Arial", 10, "bold"),
            fill=self.TEXT_COLOR,
        )
        if card.cost_belief or card.cost_fear:
            cost_text = self._format_cost(card)
            canvas.create_text(
                x + width - 10,
                y + 19,
                anchor="e",
                text=cost_text,
                font=self._get_font("Arial", 9, "bold"),
                fill=self.SECONDARY_ACCENT,
            )
        art_image = self._get_card_image(card, int(width * 0.65), 65)
        art_top = y + 36
        art_height = 70
        canvas.create_rectangle(
            x + 10,
            art_top,
            x + width - 10,
            art_top + art_height,
            fill=self.PANEL_COLOR,
            outline=self.BORDER_COLOR,
        )
        if art_image:
            canvas.create_image(x + width / 2, art_top + art_height / 2, image=art_image)
        desc_y = art_top + art_height + 6
        canvas.create_text(
            x + 12,
            desc_y,
            anchor="nw",
            text=card.text[:70] + ("..." if len(card.text) > 70 else ""),
            width=width - 24,
            font=self._get_font("Arial", 9),
            fill=self.MUTED_TEXT,
        )
        stats_y = desc_y + 32
        canvas.create_rectangle(
            x + 10,
            stats_y,
            x + width - 10,
            stats_y + 24,
            fill=self.FACTION_BANNER,
            outline=self.ACCENT_COLOR,
            width=1,
        )
        if isinstance(card, Cryptid):
            canvas.create_text(
                x + width / 2,
                stats_y + 12,
                text=f"PWR {card.stats.power}  DEF {card.stats.defense}  HP {card.current_health}/{card.stats.health}",
                font=self._get_font("Arial", 9, "bold"),
                fill=self.TEXT_COLOR,
            )
        elif isinstance(card, GodCard):
            canvas.create_text(
                x + width / 2,
                stats_y + 12,
                text=card.prayer_text or "Divinity",
                font=self._get_font("Arial", 9, "bold"),
                fill=self.TEXT_COLOR,
            )
        else:
            canvas.create_text(
                x + width / 2,
                stats_y + 12,
                text="Support",
                font=self._get_font("Arial", 9, "bold"),
                fill=self.TEXT_COLOR,
            )
        canvas.itemconfigure(rect, tags=(tag,))

    def _draw_territory_tile(
        self, canvas: tk.Canvas, territory: object, x: float, y: float, width: float, height: float
    ) -> None:
        name = getattr(territory, "name", "Territory")
        canvas.create_rectangle(x, y, x + width, y + height, fill=self.TABLE_COLOR, outline=self.ACCENT_COLOR, width=2)
        canvas.create_rectangle(
            x + 4,
            y + 4,
            x + width - 4,
            y + height - 4,
            fill=self.PANEL_COLOR,
            outline=self.BORDER_COLOR,
        )
        canvas.create_text(
            x + width / 2,
            y + height / 2,
            text=name,
            fill=self.TEXT_COLOR,
            font=("Arial", 10, "bold"),
        )

    def _draw_drop_zone(self, idx: int, layout: dict[str, object]) -> None:
        canvas = self.battlefield_canvases[idx]
        canvas.update_idletasks()
        frame_slots = [layout["active"], *layout["bench"], *layout["territories"]]
        x1 = min(slot[0] for slot in frame_slots) - 18
        y1 = min(slot[1] for slot in frame_slots) - 18
        x2 = max(slot[2] for slot in frame_slots) + 18
        y2 = max(slot[3] for slot in frame_slots) + 18
        rect_tag = f"drop_zone_{idx}_rect"
        label_tag = f"drop_zone_{idx}_label"
        self._clear_drop_zone_gradient(idx)
        self._clear_drop_zone_tooltip(idx)
        self._clear_drop_zone_slots(idx)
        if idx in self.drop_zone_items:
            rect_id, label_id = self.drop_zone_items[idx]
            canvas.delete(rect_id)
            canvas.delete(label_id)

        playmat_image = self._get_playmat_image(int(x2 - x1), int(y2 - y1))
        if playmat_image:
            bg_id = canvas.create_image(x1, y1, anchor="nw", image=playmat_image)
            self.drop_zone_background_items[idx] = bg_id
            self.drop_zone_slot_items[idx] = [bg_id]
        else:
            self.drop_zone_slot_items[idx] = []

        rect_id = canvas.create_rectangle(
            x1 + 2,
            y1 + 2,
            x2 - 2,
            y2 - 2,
            dash=(),
            outline=self.ACCENT_COLOR,
            width=2,
            fill=self._blend_color(self.TABLE_COLOR, "#000000", 0.35),
            stipple="gray50",
            tags=(rect_tag,),
        )

        slot_items: list[int] = []

        def add_slot_overlay(
            coords: tuple[float, float, float, float],
            label: str,
            fill: str,
            outline: str,
            tag: str,
        ) -> None:
            x_a, y_a, x_b, y_b = coords
            rect = canvas.create_rectangle(
                x_a,
                y_a,
                x_b,
                y_b,
                fill=fill,
                outline=outline,
                width=2,
                dash=(4, 2),
                stipple="gray50",
                tags=(tag,),
            )
            text = canvas.create_text(
                (x_a + x_b) / 2,
                y_a + 14,
                text=label,
                fill=self.TEXT_COLOR,
                font=("Arial", 10, "bold"),
                tags=(tag,),
            )
            slot_items.extend([rect, text])
            hover_fill = self._blend_color(fill, "#ffffff", 0.18)
            canvas.tag_bind(tag, "<Enter>", lambda _e, r=rect, f=hover_fill: canvas.itemconfigure(r, fill=f))
            canvas.tag_bind(tag, "<Leave>", lambda _e, r=rect, f=fill: canvas.itemconfigure(r, fill=f))

        territory_band = (
            min(slot[0] for slot in layout["territories"]) - 6,
            min(slot[1] for slot in layout["territories"]) - 6,
            max(slot[2] for slot in layout["territories"]) + 6,
            max(slot[3] for slot in layout["territories"]) + 6,
        )
        add_slot_overlay(
            territory_band,
            "Territory / Land Row",
            self._blend_color(self.FIELD_GLOW, "#000000", 0.45),
            self.FIELD_GLOW,
            f"drop_zone_{idx}_territory",
        )

        add_slot_overlay(
            layout["active"],
            "Active Summon", 
            self._blend_color(self.SECONDARY_ACCENT, "#000000", 0.55),
            self.SECONDARY_ACCENT,
            f"drop_zone_{idx}_active",
        )

        for bench_idx, bench_slot in enumerate(layout["bench"], start=1):
            add_slot_overlay(
                bench_slot,
                f"Bench {bench_idx} (Ally)",
                self._blend_color(self.ACCENT_COLOR, "#000000", 0.65),
                self.ACCENT_COLOR,
                f"drop_zone_{idx}_bench_{bench_idx}",
            )

        label_id = canvas.create_text(
            (x1 + x2) / 2,
            y1 + 16,
            text="Ritual playmat — drop cards onto matching zones",
            font=("Arial", 11, "bold"),
            fill=self.TEXT_COLOR,
            tags=(label_tag,),
        )
        self.drop_zone_slot_items[idx].extend(slot_items)
        self.drop_zone_glow_items[idx] = []
        self.drop_zone_boxes[idx] = (x1, y1, x2, y2)
        self.drop_zone_items[idx] = (rect_id, label_id)

    def _refresh_drop_zone_bounds(self) -> None:
        for idx, canvas in enumerate(self.battlefield_canvases):
            if idx not in self.drop_zone_boxes:
                continue
            x1, y1, x2, y2 = self.drop_zone_boxes[idx]
            root_x, root_y = canvas.winfo_rootx(), canvas.winfo_rooty()
            self.drop_zone_screen_bounds[idx] = (root_x + x1, root_y + y1, root_x + x2, root_y + y2)

    def _clear_drop_zone_tooltip(self, idx: int) -> None:
        ids = self.drop_zone_tooltips.pop(idx, None)
        if not ids:
            return
        canvas = self.battlefield_canvases[idx]
        for item_id in ids:
            canvas.delete(item_id)

    def _clear_drop_zone_slots(self, idx: int) -> None:
        canvas = self.battlefield_canvases[idx]
        for item_id in self.drop_zone_slot_items.get(idx, []):
            canvas.delete(item_id)
        self.drop_zone_slot_items[idx] = []
        if idx in self.drop_zone_background_items:
            canvas.delete(self.drop_zone_background_items[idx])
            self.drop_zone_background_items.pop(idx, None)

    def _show_drop_tooltip(self, idx: int, text: str, color: str | None = None) -> None:
        if idx not in self.drop_zone_boxes:
            return
        canvas = self.battlefield_canvases[idx]
        self._clear_drop_zone_tooltip(idx)
        x1, y1, x2, y2 = self.drop_zone_boxes[idx]
        tip_bg = canvas.create_rectangle(
            x1 + 10,
            y2 - 30,
            x2 - 10,
            y2 - 8,
            fill=self.PANEL_COLOR,
            outline=self.BORDER_COLOR,
        )
        tip_text = canvas.create_text(
            (x1 + x2) / 2,
            y2 - 19,
            text=text,
            fill=color or self.ALERT_COLOR,
            font=("Arial", 9, "bold"),
        )
        self.drop_zone_tooltips[idx] = (tip_bg, tip_text)
        canvas.after(1400, lambda idx=idx: self._clear_drop_zone_tooltip(idx))

    def _clear_drop_zone_gradient(self, idx: int) -> None:
        canvas = self.battlefield_canvases[idx]
        for item_id in self.drop_zone_gradient_items.get(idx, []):
            canvas.delete(item_id)
        self.drop_zone_gradient_items[idx] = []

    def _clear_drop_zone_glow(self, idx: int) -> None:
        canvas = self.battlefield_canvases[idx]
        for item_id in self.drop_zone_glow_items.get(idx, []):
            canvas.delete(item_id)
        self.drop_zone_glow_items[idx] = []

    @staticmethod
    def _blend_color(base: str, mix: str, ratio: float) -> str:
        def to_rgb(value: str) -> tuple[int, int, int]:
            value = value.lstrip("#")
            return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)

        base_r, base_g, base_b = to_rgb(base)
        mix_r, mix_g, mix_b = to_rgb(mix)
        r = int(base_r * (1 - ratio) + mix_r * ratio)
        g = int(base_g * (1 - ratio) + mix_g * ratio)
        b = int(base_b * (1 - ratio) + mix_b * ratio)
        return f"#{r:02x}{g:02x}{b:02x}"

    def _create_vertical_gradient(
        self, canvas: tk.Canvas, x1: int, y1: int, x2: int, y2: int, start: str, end: str, steps: int = 16
    ) -> list[int]:
        items: list[int] = []
        height = y2 - y1
        for i in range(steps):
            ratio = i / max(steps - 1, 1)
            color = self._blend_color(start, end, ratio)
            rect = canvas.create_rectangle(x1, y1 + (height / steps) * i, x2, y1 + (height / steps) * (i + 1), outline="", fill=color)
            items.append(rect)
        return items

    def _get_playmat_image(self, max_width: int, max_height: int) -> Optional[tk.PhotoImage]:
        path = Path("assets/board/playmat_portal.png")
        if not path.exists():
            return None

        cache_key = (str(path), max_width, max_height)
        if cache_key in self._playmat_image_cache:
            return self._playmat_image_cache[cache_key]

        try:
            image = Image.open(path).convert("RGBA")
        except (OSError, FileNotFoundError):
            return None

        width, height = image.size
        target_w = max(max_width, 1)
        target_h = max(max_height, 1)
        scale = max(target_w / width, target_h / height)
        new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
        resized = image.resize(new_size, Image.LANCZOS)
        cropped = resized.crop((0, 0, target_w, target_h))
        tk_img = ImageTk.PhotoImage(cropped)
        self._playmat_image_cache[cache_key] = tk_img
        return tk_img

    def _apply_drop_zone_glow(self, idx: int, base_color: str) -> None:
        if idx not in self.drop_zone_boxes:
            return
        canvas = self.battlefield_canvases[idx]
        self._clear_drop_zone_glow(idx)
        x1, y1, x2, y2 = self.drop_zone_boxes[idx]
        steps = 5
        items: list[int] = []
        for i in range(steps):
            ratio = (i + 1) / (steps + 1)
            color = self._blend_color(base_color, "#ffffff", ratio * 0.6)
            inset = 2 + i * 3
            rect = canvas.create_rectangle(
                x1 + inset,
                y1 + inset,
                x2 - inset,
                y2 - inset,
                fill=color,
                outline="",
            )
            items.append(rect)
        self.drop_zone_glow_items[idx] = items

    def _format_cost_text(self, card: Card) -> str:
        parts: list[str] = []
        if card.cost_belief:
            parts.append(f"{card.cost_belief} Belief")
        if card.cost_fear:
            parts.append(f"{card.cost_fear} Fear")
        return "Cost: " + (", ".join(parts) if parts else "Free")

    def _affordability_info(self, card: Optional[Card]) -> tuple[bool, str]:
        if not card:
            return True, ""
        pool = self.game.players[self.human_index].resources
        missing_fear = max(card.cost_fear - pool.fear, 0)
        missing_belief = max(card.cost_belief - pool.belief, 0)
        if not missing_fear and not missing_belief:
            return True, "Affordable"
        missing_parts = []
        if missing_belief:
            missing_parts.append(f"{missing_belief} Belief")
        if missing_fear:
            missing_parts.append(f"{missing_fear} Fear")
        return False, f"Need {', '.join(missing_parts)}"

    def _highlight_drop_zone(self, active_idx: Optional[int], card: Optional[Card] = None) -> None:
        if active_idx is None:
            for idx in list(self.drop_zone_tooltips.keys()):
                self._clear_drop_zone_tooltip(idx)
        for idx, items in self.drop_zone_items.items():
            rect_id, label_id = items
            canvas = self.battlefield_canvases[idx]
            is_active = active_idx == idx
            display_card = card if is_active else None
            affordable, status = self._affordability_info(display_card)
            if is_active and display_card:
                cost_text = self._format_cost_text(display_card)
                label = f"Release to play — {cost_text} ({status})"
            else:
                label = "Drop to play"
            fill = self.SURFACE_COLOR
            outline = self.SECONDARY_ACCENT
            text_color = self.TEXT_COLOR
            dash = (3, 2)
            width = 1
            if is_active:
                if display_card and not affordable:
                    fill = self.ALERT_COLOR
                    outline = self.ALERT_COLOR
                    text_color = self.BG_COLOR
                    self._clear_drop_zone_glow(idx)
                else:
                    fill = self.SURFACE_COLOR
                    outline = self.ACCENT_COLOR
                    text_color = self.TEXT_COLOR
                    self._apply_drop_zone_glow(idx, self.ACCENT_COLOR)
                dash = ()
                width = 3
            else:
                self._clear_drop_zone_glow(idx)
            canvas.itemconfigure(rect_id, fill=fill, outline=outline, dash=dash, width=width)
            canvas.itemconfigure(label_id, fill=text_color, text=label)

    def _animate_drop(self, idx: int) -> None:
        if idx not in self.drop_zone_items:
            return
        rect_id, _ = self.drop_zone_items[idx]
        canvas = self.battlefield_canvases[idx]
        original_fill = canvas.itemcget(rect_id, "fill")
        pulse_colors = [self.ACCENT_COLOR, self.SECONDARY_ACCENT, str(original_fill)]

        def step(colors: list[str]) -> None:
            if not colors:
                return
            color = colors.pop(0)
            canvas.itemconfigure(rect_id, fill=color)
            canvas.after(90, lambda: step(colors))

        step(pulse_colors)

    def _get_card_image(self, card: Card, max_width: int, max_height: int) -> Optional[tk.PhotoImage]:
        path = Path(card.asset_path())
        if not path.exists():
            return None

        cache_key = (str(path), max_width, max_height)
        if cache_key in self._image_cache:
            return self._image_cache[cache_key]

        try:
            image = Image.open(path).convert("RGBA")
        except (OSError, FileNotFoundError):
            return None

        width, height = image.size
        if width > max_width or height > max_height:
            scale = min(max_width / max(width, 1), max_height / max(height, 1))
            new_width = max(int(width * scale), 1)
            new_height = max(int(height * scale), 1)
            image = image.resize((new_width, new_height), Image.LANCZOS)

        tk_image = ImageTk.PhotoImage(image)
        self._image_cache[cache_key] = tk_image
        return tk_image

    def _get_font(self, family: str, size: int, weight: str = "normal") -> tkfont.Font:
        key = (family, size, weight)
        if key not in self._font_cache:
            self._font_cache[key] = tkfont.Font(family=family, size=size, weight=weight)
        return self._font_cache[key]

    def _create_drag_preview(self, card: Optional[Card]) -> None:
        if not card:
            return
        self._destroy_drag_preview()
        self.drag_overlay_card = card
        self.root.update_idletasks()
        root_w = max(self.root.winfo_width(), 1)
        root_h = max(self.root.winfo_height(), 1)
        root_x, root_y = self.root.winfo_rootx(), self.root.winfo_rooty()
        self.drag_overlay = tk.Toplevel(self.root)
        self.drag_overlay.overrideredirect(True)
        self.drag_overlay.attributes("-topmost", True)
        try:
            self.drag_overlay.attributes("-alpha", 0.9)
        except tk.TclError:
            pass
        try:
            self.drag_overlay.attributes("-transparentcolor", "systemTransparent")
            bg_color = "systemTransparent"
        except tk.TclError:
            bg_color = ""
        self.drag_overlay.configure(bg=bg_color)
        self.drag_overlay.geometry(f"{root_w}x{root_h}+{root_x}+{root_y}")
        try:
            canvas = tk.Canvas(
                self.drag_overlay,
                width=root_w,
                height=root_h,
                bg=bg_color or "white",
                highlightthickness=0,
            )
        except tk.TclError:
            canvas = tk.Canvas(self.drag_overlay, width=root_w, height=root_h, bg="white", highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        self.drag_overlay_canvas = canvas
        self.drag_overlay.lift()
        self.drag_overlay.bind("<B1-Motion>", self._on_global_drag_motion)
        self.drag_overlay.bind("<ButtonRelease-1>", self._on_global_button_release)
        self._move_drag_preview(self.root.winfo_pointerx(), self.root.winfo_pointery())

    def _move_drag_preview(self, x_root: int, y_root: int) -> None:
        if not self.drag_overlay or not self.drag_overlay_canvas or not self.drag_overlay_card:
            return
        self.root.update_idletasks()
        root_w = max(self.root.winfo_width(), 1)
        root_h = max(self.root.winfo_height(), 1)
        root_x, root_y = self.root.winfo_rootx(), self.root.winfo_rooty()
        self.drag_overlay.geometry(f"{root_w}x{root_h}+{root_x}+{root_y}")
        self.drag_overlay.lift()
        canvas = self.drag_overlay_canvas
        canvas.configure(width=root_w, height=root_h)
        canvas.delete("all")

        card_w = 170
        card_h = 220
        snap_x, snap_y = x_root, y_root
        if self.drag_state.hovered_target is not None:
            bounds = self.drop_zone_screen_bounds.get(self.drag_state.hovered_target)
            if bounds:
                snap_x = (bounds[0] + bounds[2]) / 2
                snap_y = (bounds[1] + bounds[3]) / 2

        local_x = snap_x - self.drag_overlay.winfo_rootx()
        local_y = snap_y - self.drag_overlay.winfo_rooty()
        x1 = local_x - card_w / 2
        y1 = local_y - card_h / 2
        x2 = x1 + card_w
        y2 = y1 + card_h

        header_font = self._get_font("Arial", 10, "bold")
        body_font = self._get_font("Arial", 9)
        tiny_font = self._get_font("Arial", 8, "bold")

        canvas.create_rectangle(x1 + 6, y1 + 10, x2 + 6, y2 + 10, fill="#c4c8d4", outline="")
        canvas.create_rectangle(x1, y1, x2, y2, fill="#f9fbff", outline="#6666aa", width=2)
        canvas.create_rectangle(x1 + 6, y1 + 6, x2 - 6, y2 - 6, fill="#ffffff", outline="#a2a8c5", width=1)
        canvas.create_rectangle(x1 + 6, y1 + 6, x2 - 6, y1 + 36, fill="#e7ecff", outline="",)
        canvas.create_text(x1 + 12, y1 + 22, text=self.drag_overlay_card.name, anchor="w", font=header_font)

        cost_x = x2 - 10
        if self.drag_overlay_card.cost_belief:
            canvas.create_oval(cost_x - 20, y1 + 10, cost_x - 6, y1 + 24, fill="#ffe8b3", outline="#c08000", width=1)
            canvas.create_text(cost_x - 13, y1 + 17, text=str(self.drag_overlay_card.cost_belief), font=tiny_font, fill="#7a4a00")
        if self.drag_overlay_card.cost_fear:
            canvas.create_oval(cost_x - 20, y1 + 10, cost_x - 6, y1 + 24, fill="#c9b7f7", outline="#6540c2", width=1)
            canvas.create_text(cost_x - 13, y1 + 17, text=str(self.drag_overlay_card.cost_fear), font=tiny_font, fill="#3a1b6f")

        image = self._get_card_image(self.drag_overlay_card, 110, 80)
        image_top = y1 + 44
        image_height = 80
        if image:
            canvas.create_rectangle(x1 + 10, image_top, x2 - 10, image_top + image_height, fill="#eef1ff", outline="#d0d4ee")
            canvas.create_image((x1 + x2) / 2, image_top + image_height / 2, image=image)

        body_top = image_top + image_height + 6
        text_block_height = 52
        body_text = (self.drag_overlay_card.text or "")[:160]
        canvas.create_text(
            x1 + 12,
            body_top,
            anchor="nw",
            text=body_text + ("..." if len(self.drag_overlay_card.text or "") > 160 else ""),
            width=card_w - 24,
            font=body_font,
        )

        stats_top = body_top + text_block_height
        if isinstance(self.drag_overlay_card, Cryptid):
            stats = self.drag_overlay_card.stats
            stat_box_height = 28
            canvas.create_rectangle(x1 + 10, stats_top, x2 - 10, stats_top + stat_box_height, fill="#eef7ff", outline="#c3d8ff")
            canvas.create_text(
                (x1 + x2) / 2,
                stats_top + stat_box_height / 2,
                text=f"PWR {stats.power}  DEF {stats.defense}  HP {self.drag_overlay_card.current_health}/{stats.health}",
                font=self._get_font("Arial", 9, "bold"),
            )
            move_top = stats_top + stat_box_height + 4
            moves_to_show = self.drag_overlay_card.moves[:2]
            for move in moves_to_show:
                canvas.create_text(
                    x1 + 12,
                    move_top,
                    anchor="nw",
                    text=move.describe(),
                    width=card_w - 24,
                    font=self._get_font("Arial", 8),
                )
                move_top += 18
        else:
            canvas.create_rectangle(x1 + 10, stats_top, x2 - 10, stats_top + 28, fill="#f9f1ea", outline="#e2c7a6")
            canvas.create_text(x1 + 12, stats_top + 8, anchor="nw", text="Support", font=self._get_font("Arial", 9, "bold"))

        self.drag_overlay_bounds = (
            int(self.drag_overlay.winfo_rootx() + x1),
            int(self.drag_overlay.winfo_rooty() + y1),
            int(self.drag_overlay.winfo_rootx() + x2),
            int(self.drag_overlay.winfo_rooty() + y2),
        )

    def _destroy_drag_preview(self) -> None:
        if self.drag_overlay:
            self.drag_overlay.destroy()
        self.drag_overlay = None
        self.drag_overlay_canvas = None
        self.drag_overlay_bounds = None
        self.drag_overlay_card = None

    def _update_hover_target(self, x_root: int, y_root: int) -> None:
        target_idx: Optional[int] = None
        overlay_bounds = self.drag_overlay_bounds
        for idx in (self.human_index,):
            bounds = self.drop_zone_screen_bounds.get(idx)
            if not bounds:
                continue
            if overlay_bounds and self._bounds_intersect(overlay_bounds, bounds):
                target_idx = idx
                break
            x1, y1, x2, y2 = bounds
            if x1 <= x_root <= x2 and y1 <= y_root <= y2:
                target_idx = idx
                break
        if target_idx != self.drag_state.hovered_target:
            self.drag_state.hovered_target = target_idx
            self._highlight_drop_zone(target_idx, self.drag_overlay_card)

    def _render_hand(self, idx: int) -> None:
        canvas = self.hand_canvases[idx]
        canvas.delete("all")
        player = self.game.players[idx]
        self.card_tags = {key: value for key, value in self.card_tags.items() if key[0] != idx}
        canvas.update_idletasks()

        hand_size = len(player.hand)
        if hand_size == 0:
            return

        card_width = 150
        card_height = 190
        overlap = 70
        start_x = max((canvas.winfo_width() - (card_width + overlap * (hand_size - 1))) / 2, 10)
        base_y = 8
        center_index = (hand_size - 1) / 2

        header_font = self._get_font("Arial", 10, "bold")
        body_font = self._get_font("Arial", 9)
        tiny_font = self._get_font("Arial", 8, "bold")

        for i, card in enumerate(player.hand):
            x = start_x + i * overlap
            y = base_y + abs(i - center_index) * 2
            tag = f"hand_{idx}_{i}"
            is_selected = self.selected_player_idx == idx and self.selected_tag == tag
            is_hovered = self._hovered_hand_tag == tag
            scale = 1.08 if (is_hovered or is_selected) else 1.0
            lift = 14 if (is_hovered or is_selected) else 0

            scaled_w = card_width * scale
            scaled_h = card_height * scale
            x_adjust = x - (scaled_w - card_width) / 2
            y_adjust = y - lift - (scaled_h - card_height) / 2
            shadow = canvas.create_rectangle(
                x_adjust + 6,
                y_adjust + 10,
                x_adjust + scaled_w + 6,
                y_adjust + scaled_h + 10,
                fill=self.SHADOW_COLOR,
                outline="",
                tags=(tag,),
            )
            frame = canvas.create_rectangle(
                x_adjust,
                y_adjust,
                x_adjust + scaled_w,
                y_adjust + scaled_h,
                fill=self.CARD_FACE,
                outline=self.ACCENT_COLOR if is_selected else self.SECONDARY_ACCENT,
                width=3 if is_selected else 2,
                tags=(tag,),
            )
            canvas.create_rectangle(
                x_adjust + 6,
                y_adjust + 6,
                x_adjust + scaled_w - 6,
                y_adjust + scaled_h - 6,
                fill=self.CARD_INNER,
                outline=self.BORDER_COLOR,
                width=1,
                tags=(tag,),
            )

            canvas.create_rectangle(
                x_adjust + 6,
                y_adjust + 6,
                x_adjust + scaled_w - 6,
                y_adjust + 34,
                fill=self.CARD_TYPE_STRIP,
                outline="",
                tags=(tag,),
            )
            canvas.create_text(
                x_adjust + 12,
                y_adjust + 20,
                text=card.name,
                anchor="w",
                font=header_font,
                fill=self.TEXT_COLOR,
                tags=(tag,),
            )

            cost_x = x_adjust + scaled_w - 10
            if card.cost_belief:
                canvas.create_oval(
                    cost_x - 20,
                    y_adjust + 10,
                    cost_x - 6,
                    y_adjust + 24,
                    fill="#f5e4b5",
                    outline=self.ACCENT_COLOR,
                    width=1,
                    tags=(tag,),
                )
                canvas.create_text(
                    cost_x - 13,
                    y_adjust + 17,
                    text=str(card.cost_belief),
                    font=tiny_font,
                    fill="#3a280c",
                    tags=(tag,),
                )
                cost_x -= 22
            if card.cost_fear:
                canvas.create_oval(
                    cost_x - 20,
                    y_adjust + 10,
                    cost_x - 6,
                    y_adjust + 24,
                    fill="#c8ddff",
                    outline=self.SECONDARY_ACCENT,
                    width=1,
                    tags=(tag,),
                )
                canvas.create_text(
                    cost_x - 13,
                    y_adjust + 17,
                    text=str(card.cost_fear),
                    font=tiny_font,
                    fill=self.BG_COLOR,
                    tags=(tag,),
                )

            image = self._get_card_image(card, 100, 70)
            image_top = y_adjust + 40
            image_height = 70
            if image:
                canvas.create_rectangle(
                    x_adjust + 10,
                    image_top,
                    x_adjust + scaled_w - 10,
                    image_top + image_height,
                    fill=self.PANEL_COLOR,
                    outline=self.BORDER_COLOR,
                    tags=(tag,),
                )
                canvas.create_image(
                    x_adjust + scaled_w / 2,
                    image_top + image_height / 2,
                    image=image,
                    tags=(tag,),
                )
            body_top = image_top + image_height + 6
            text_block_height = 44
            canvas.create_text(
                x_adjust + 12,
                body_top,
                anchor="nw",
                text=(card.text or "")[:120] + ("..." if len(card.text) > 120 else ""),
                width=scaled_w - 24,
                font=body_font,
                fill=self.MUTED_TEXT,
                tags=(tag,),
            )

            stats_top = body_top + text_block_height
            if isinstance(card, Cryptid):
                stats = card.stats
                stat_box_height = 26
                canvas.create_rectangle(
                    x_adjust + 10,
                    stats_top,
                    x_adjust + scaled_w - 10,
                    stats_top + stat_box_height,
                    fill=self.CARD_TYPE_STRIP,
                    outline=self.ACCENT_COLOR,
                    tags=(tag,),
                )
                canvas.create_text(
                    x_adjust + scaled_w / 2,
                    stats_top + stat_box_height / 2,
                    text=f"PWR {stats.power}  DEF {stats.defense}  HP {card.current_health}/{stats.health}",
                    font=self._get_font("Arial", 9, "bold"),
                    fill=self.TEXT_COLOR,
                    tags=(tag,),
                )

                move_top = stats_top + stat_box_height + 4
                moves_to_show = card.moves[:2]
                for move in moves_to_show:
                    move_text = move.describe()
                    canvas.create_text(
                        x_adjust + 12,
                        move_top,
                        anchor="nw",
                        text=move_text,
                        width=scaled_w - 24,
                        font=self._get_font("Arial", 8),
                        fill=self.MUTED_TEXT,
                        tags=(tag,),
                    )
                    move_top += 18
            else:
                canvas.create_rectangle(
                    x_adjust + 10,
                    stats_top,
                    x_adjust + scaled_w - 10,
                    stats_top + 26,
                    fill=self.PANEL_COLOR,
                    outline=self.BORDER_COLOR,
                    tags=(tag,),
                )
                canvas.create_text(
                    x_adjust + 12,
                    stats_top + 6,
                    anchor="nw",
                    text="Support",
                    font=self._get_font("Arial", 9, "bold"),
                    fill=self.TEXT_COLOR,
                    tags=(tag,),
                )

            self.card_tags[(idx, tag)] = card
            canvas.tag_bind(tag, "<Button-1>", lambda e, t=tag, p=idx: self._select_card(p, t))
            canvas.tag_bind(tag, "<ButtonPress-1>", lambda e, t=tag, p=idx: self._start_drag(e, p, t))
            canvas.tag_bind(tag, "<B1-Motion>", lambda e, t=tag, p=idx: self._drag(e, p, t))
            canvas.tag_bind(tag, "<ButtonRelease-1>", lambda e, t=tag, p=idx: self._end_drag(e, p, t))
            canvas.tag_bind(tag, "<Enter>", lambda e, t=tag, p=idx: self._set_hover(t, p))
            canvas.tag_bind(tag, "<Leave>", lambda e, t=tag, p=idx: self._clear_hover(t, p))
            canvas.tag_raise(tag)

        if self.selected_player_idx == idx:
            if self.selected_card is None or self.selected_card not in player.hand:
                self._clear_selection()
            else:
                new_index = player.hand.index(self.selected_card)
                self.selected_tag = f"hand_{idx}_{new_index}"
                self._apply_selection_highlight()

    def _set_hover(self, tag: str, player_idx: int) -> None:
        if player_idx != self.human_index:
            return
        if self._hovered_hand_tag == tag:
            return
        self._hovered_hand_tag = tag
        self._render_hand(player_idx)

    def _clear_hover(self, tag: str, player_idx: int) -> None:
        if self._hovered_hand_tag != tag:
            return
        self._hovered_hand_tag = None
        self._render_hand(player_idx)

    def _select_card(self, player_idx: int, tag: str) -> None:
        if player_idx != self.human_index:
            return
        card = self.card_tags.get((player_idx, tag))
        if not card:
            self._clear_selection()
            return
        self._clear_selection()
        self.selected_card = card
        self.selected_player_idx = player_idx
        self.selected_tag = tag
        self._apply_selection_highlight()
        self._log(f"Selected {self.selected_card.name} from {self.game.players[player_idx].name}'s hand.")
        self._show_card_details(card)

    def _start_drag(self, event: tk.Event, player_idx: int, tag: str) -> None:
        if self.active_index != player_idx or player_idx != self.human_index:
            return
        self.drag_state = DragState(player_index=player_idx, tag=tag, last_x=event.x, last_y=event.y)
        canvas = self.hand_canvases[player_idx]
        canvas.tag_raise(tag)
        self._create_drag_preview(self.card_tags.get((player_idx, tag)))
        self._refresh_drop_zone_bounds()
        self.root.bind("<B1-Motion>", self._on_global_drag_motion)
        self.root.bind("<ButtonRelease-1>", self._on_global_button_release)

    def _drag(self, event: tk.Event, player_idx: int, tag: str) -> None:
        if self.drag_state.tag != tag or self.drag_state.player_index != player_idx:
            return
        canvas = self.hand_canvases[player_idx]
        dx = event.x - self.drag_state.last_x
        dy = event.y - self.drag_state.last_y
        canvas.move(tag, dx, dy)
        self.drag_state.last_x = event.x
        self.drag_state.last_y = event.y
        self._move_drag_preview(event.x_root, event.y_root)
        self._update_hover_target(event.x_root, event.y_root)

    def _end_drag(self, event: tk.Event, player_idx: int, tag: str) -> None:
        if self.drag_state.tag != tag or self.drag_state.player_index != player_idx:
            return
        card = self.card_tags.get((player_idx, tag))
        if not card:
            return
        should_reset_highlight = True
        if self.drag_state.hovered_target is not None:
            affordable, status = self._affordability_info(card)
            if not affordable:
                self._show_drop_tooltip(self.drag_state.hovered_target, status)
            elif self._play_card(player_idx, card):
                self._clear_selection()
                self._animate_drop(self.drag_state.hovered_target)
                should_reset_highlight = False
        if should_reset_highlight:
            self._highlight_drop_zone(None)
        self._destroy_drag_preview()
        self._render_hand(player_idx)
        self.drag_state = DragState()
        self.root.unbind("<B1-Motion>")
        self.root.unbind("<ButtonRelease-1>")

    def _on_global_drag_motion(self, event: tk.Event) -> None:
        if not self.drag_state.tag:
            return
        self._move_drag_preview(event.x_root, event.y_root)
        self._update_hover_target(event.x_root, event.y_root)

    def _on_global_button_release(self, event: tk.Event) -> None:
        if not self.drag_state.tag or self.drag_state.player_index is None:
            return
        self._end_drag(event, self.drag_state.player_index, self.drag_state.tag)

    @staticmethod
    def _bounds_intersect(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
        ax1, ay1, ax2, ay2 = a
        bx1, by1, bx2, by2 = b
        return not (ax2 < bx1 or bx2 < ax1 or ay2 < by1 or by2 < ay1)

    def draw_card(self) -> None:
        if not self._assert_human_turn():
            return
        player = self.game.players[self.human_index]
        messages = player.draw()
        for msg in messages:
            self._log(msg)
        self._render_player(self.human_index)

    def play_selected(self) -> None:
        if not self.selected_card or self.selected_player_idx != self.human_index:
            self._log("No card selected.")
            return
        if not self._assert_human_turn():
            return
        player = self.game.players[self.selected_player_idx]
        if self.selected_card not in player.hand:
            self._log("Selected card is no longer in hand.")
            self._clear_selection()
            return
        if self._play_card(self.selected_player_idx, self.selected_card):
            self._clear_selection()

    def _play_card(self, player_idx: int, card: Card) -> bool:
        player = self.game.players[player_idx]
        if card not in player.hand:
            self._log("Card is no longer in hand.")
            return False

        message: Optional[str] = None
        if isinstance(card, TerritoryCard):
            player.hand.remove(card)
            message = player.settle_territory_card(card, self.game.stack)
        elif isinstance(card, Cryptid):
            if not card.can_play(player.resources):
                self._log(f"Cannot afford {card.name}.")
                return False
            player.hand.remove(card)
            message = player.summon(card, self.game.stack)
        elif isinstance(card, EventCard):
            if not card.can_play(player.resources):
                self._log(f"Cannot afford {card.name}.")
                return False
            player.hand.remove(card)
            message = player.cast_event(card, self.game.stack)
        elif isinstance(card, GodCard):
            if not card.can_play(player.resources):
                self._log(f"Cannot afford {card.name}.")
                return False
            player.hand.remove(card)
            message = player.play_god(card, self.game.stack)

        if message:
            self._log(message)
        self.resolve_stack()
        self._render_player(player_idx)
        return True

    def _apply_selection_highlight(self) -> None:
        if self.selected_player_idx is None or not self.selected_tag:
            return
        canvas = self.hand_canvases[self.selected_player_idx]
        if canvas.find_withtag(self.selected_tag):
            canvas.itemconfigure(self.selected_tag, outline=self.ACCENT_COLOR, width=3)

    def _clear_selection(self) -> None:
        if self.selected_player_idx is not None and self.selected_tag:
            canvas = self.hand_canvases[self.selected_player_idx]
            if canvas.find_withtag(self.selected_tag):
                canvas.itemconfigure(self.selected_tag, outline=self.SECONDARY_ACCENT, width=1)
        self.selected_card = None
        self.selected_player_idx = None
        self.selected_tag = None
        self._close_detail_window()

    def _format_cost(self, card: Card) -> str:
        parts = []
        if card.cost_fear:
            parts.append(f"{card.cost_fear} Fear")
        if card.cost_belief:
            parts.append(f"{card.cost_belief} Belief")
        return ", ".join(parts) if parts else "Free"

    def _close_detail_window(self) -> None:
        if self.detail_window:
            try:
                self.detail_window.grab_release()
            except tk.TclError:
                pass
            self.detail_window.destroy()
            self.detail_window = None
        self._detail_focusable = []

    def _show_card_details(self, card: Card) -> None:
        self._close_detail_window()
        self.root.update_idletasks()
        root_w = max(self.root.winfo_width(), 1)
        root_h = max(self.root.winfo_height(), 1)
        root_x, root_y = self.root.winfo_rootx(), self.root.winfo_rooty()

        overlay = tk.Toplevel(self.root)
        overlay.overrideredirect(True)
        overlay.geometry(f"{root_w}x{root_h}+{root_x}+{root_y}")
        overlay.attributes("-topmost", True)
        self.detail_window = overlay

        canvas = tk.Canvas(overlay, width=root_w, height=root_h, highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        canvas.create_rectangle(0, 0, root_w, root_h, fill="#000000", outline="", stipple="gray50")

        anchor_x, anchor_y = self._detail_anchor_position(root_x, root_y)

        card_width, card_height = 360, 520
        anchor_x = min(max(card_width / 2 + 12, anchor_x), root_w - card_width / 2 - 12)
        anchor_y = min(max(card_height / 2 + 12, anchor_y), root_h - card_height / 2 - 12)

        frame = tk.Frame(canvas, bg="#fefcf7", bd=0)
        canvas.create_window(anchor_x, anchor_y, window=frame)

        card_canvas = tk.Canvas(frame, width=card_width, height=card_height, bg="#fefcf7", highlightthickness=0)
        card_canvas.pack()
        self._draw_full_card(card_canvas, card, card_width, card_height)

        close_btn = tk.Button(frame, text="Close", command=self._close_detail_window)
        close_btn.pack(pady=(8, 0))

        frame.bind("<Button-1>", lambda e: "break")

        overlay.bind("<Escape>", lambda e: self._close_detail_window())
        overlay.bind("<Button-1>", lambda e: self._close_detail_window())
        card_canvas.bind("<Button-1>", lambda e: "break")
        close_btn.bind("<Button-1>", lambda e: "break")

        self._detail_focusable = [close_btn]
        overlay.bind("<KeyPress-Tab>", self._handle_overlay_tab)
        overlay.bind("<KeyPress-ISO_Left_Tab>", self._handle_overlay_tab)
        overlay.bind("<KeyPress-Escape>", lambda e: self._close_detail_window())
        overlay.grab_set()
        close_btn.focus_set()

    def _detail_anchor_position(self, root_x: int, root_y: int) -> tuple[float, float]:
        anchor_canvas = self.hand_canvases[self.active_index]
        if not anchor_canvas.winfo_ismapped():
            anchor_canvas = self.battlefield_canvases[self.active_index]
        anchor_canvas.update_idletasks()
        anchor_x = anchor_canvas.winfo_rootx() - root_x + anchor_canvas.winfo_width() / 2
        anchor_y = anchor_canvas.winfo_rooty() - root_y + anchor_canvas.winfo_height() / 2
        return anchor_x, anchor_y

    def _draw_full_card(self, canvas: tk.Canvas, card: Card, width: int, height: int) -> None:
        canvas.delete("all")
        pad = 14
        canvas.create_rectangle(0, 0, width, height, fill="#f4ede2", outline="#b4976a", width=2)
        canvas.create_rectangle(6, 6, width - 6, height - 6, outline="#d1c4a4", width=1)

        name_font = self._get_font("Arial", 18, "bold")
        body_font = self._get_font("Arial", 10)
        italic_font = self._get_font("Arial", 10, "bold")

        canvas.create_text(pad, pad, anchor="nw", text=card.name, font=name_font, fill="#2b1e08")
        type_cost = f"{card.type.name.title()} — Cost: {self._format_cost(card)}"
        canvas.create_text(pad, pad + 28, anchor="nw", text=type_cost, font=self._get_font("Arial", 11))

        info_y = pad + 52
        if card.faction:
            canvas.create_text(pad, info_y, anchor="nw", text=f"Faction: {card.faction}", font=body_font)
            info_y += 18
        if card.tags:
            canvas.create_text(pad, info_y, anchor="nw", text=f"Tags: {', '.join(card.tags)}", font=body_font)
            info_y += 18

        art_height = 170
        image = self._get_card_image(card, width - pad * 2, art_height)
        if image:
            canvas.create_rectangle(pad, info_y, width - pad, info_y + art_height, fill="#f7f9ff", outline="#d4d8e8")
            canvas.create_image((width) / 2, info_y + art_height / 2, image=image)
        info_y += art_height + 12

        text_block = card.text or ""
        if isinstance(card, EventCard) and card.impact_text:
            text_block = card.impact_text

        if text_block:
            text_id = canvas.create_text(
                pad,
                info_y,
                anchor="nw",
                text=text_block,
                width=width - pad * 2,
                font=body_font,
                justify=tk.LEFT,
            )
            bbox = canvas.bbox(text_id)
            info_y = (bbox[3] + 12) if bbox else info_y + 72

        if isinstance(card, TerritoryCard):
            yields = []
            if card.fear_yield:
                yields.append(f"{card.fear_yield} Fear")
            if card.belief_yield:
                yields.append(f"{card.belief_yield} Belief")
            yield_text = ", ".join(yields) if yields else "No yield"
            canvas.create_text(pad, info_y, anchor="nw", text=f"Yields: {yield_text}", font=italic_font)
            info_y += 22

        if isinstance(card, Cryptid):
            stats = card.stats
            canvas.create_rectangle(pad, info_y, width - pad, info_y + 34, fill="#eef6ff", outline="#c6d9f2")
            canvas.create_text(
                width / 2,
                info_y + 17,
                text=f"PWR {stats.power}  DEF {stats.defense}  HP {card.current_health}/{stats.health}",
                font=italic_font,
                fill="#1c3e7a",
            )
            info_y += 42
            if card.moves:
                canvas.create_text(pad, info_y, anchor="nw", text="Moves", font=italic_font)
                info_y += 18
                for move in card.moves:
                    canvas.create_text(
                        pad,
                        info_y,
                        anchor="nw",
                        text=move.describe(),
                        width=width - pad * 2,
                        font=body_font,
                        justify=tk.LEFT,
                    )
                    info_y += 22

        if isinstance(card, GodCard) and card.prayer_text:
            canvas.create_text(
                pad,
                info_y,
                anchor="nw",
                text=f"Prayer: {card.prayer_text}",
                width=width - pad * 2,
                font=body_font,
                justify=tk.LEFT,
            )
            info_y += 38

    def _handle_overlay_tab(self, event: tk.Event) -> str:
        if not self.detail_window:
            return "break"
        focusables = [w for w in self._detail_focusable if w.winfo_viewable()]
        if not focusables:
            return "break"
        current = self.detail_window.focus_get()
        try:
            idx = focusables.index(current)
        except ValueError:
            idx = 0
        direction = -1 if event.state & 0x1 else 1
        next_idx = (idx + direction) % len(focusables)
        focusables[next_idx].focus_set()
        return "break"

    def play_queued_territory(self) -> None:
        if not self._assert_human_turn():
            return
        player = self.game.players[self.human_index]
        if not player.territory_queue:
            self._log("No queued territory to play.")
            return
        territory = player.territory_queue.pop(0)
        self._log(player.play_territory(territory, self.game.stack))
        self.resolve_stack()
        self._render_player(self.human_index)

    def pray(self) -> None:
        if not self._assert_human_turn():
            return
        player = self.game.players[self.human_index]
        opponent = self.game.players[self.cpu_index]
        messages = player.pray_with_gods(opponent, self.game.stack)
        if not messages:
            self._log("No Gods to pray to.")
        for msg in messages:
            self._log(msg)
        self.resolve_stack()
        self._render_player(self.human_index)
        self._render_player(self.cpu_index)

    def resolve_stack(self) -> None:
        for msg in self.game.stack.resolve_all():
            self._log(msg)
        self._render_player(0)
        self._render_player(1)

    def end_turn(self) -> None:
        if not self._assert_human_turn():
            return
        self._log(f"{self.game.players[self.human_index].name} ends the turn.")
        self.active_index = self.cpu_index
        self._update_active_label()
        self._render_player(0)
        self._render_player(1)
        self._run_cpu_turn()

    def _run_cpu_turn(self) -> None:
        cpu = self.game.players[self.cpu_index]
        human = self.game.players[self.human_index]
        self._log(f"{cpu.name}'s turn begins.")
        for msg in cpu.draw():
            self._log(msg)
        if cpu.territory_queue:
            territory = cpu.territory_queue.pop(0)
            self._log(cpu.play_territory(territory, self.game.stack))
        if cpu.hand:
            self._log(cpu.play_first_affordable(self.game.stack))
        self.resolve_stack()
        prayers = cpu.pray_with_gods(human, self.game.stack)
        for msg in prayers:
            self._log(msg)
        self.resolve_stack()
        self._log(f"{cpu.name} ends the turn.")
        self.active_index = self.human_index
        self._update_active_label()
        self._render_player(0)
        self._render_player(1)
        self._log(f"It is now {human.name}'s turn.")

    def _assert_human_turn(self) -> bool:
        if self.active_index != self.human_index:
            self._log("It's not your turn.")
            return False
        return True

    def _update_active_label(self) -> None:
        self.active_label.configure(text=f"Active player: {self.game.players[self.active_index].name}")

    def _log(self, message: str) -> None:
        self.log_widget.configure(state=tk.NORMAL)
        self.log_widget.insert(tk.END, message + "\n")
        self.log_widget.see(tk.END)
        self.log_widget.configure(state=tk.DISABLED)

    def run(self) -> None:
        self.root.mainloop()


if __name__ == "__main__":
    gui = GameGUI()
    gui.run()
