"""Tkinter GUI for a lightweight hands-on card demo."""
from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from typing import Dict, Optional

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
    def __init__(self, deck_template: str = "balanced") -> None:
        self.root = tk.Tk()
        self.root.title("Cryptid TCG Prototype")
        self.game: GameState = initial_game(deck_template)
        self.cpu_index: int = 0
        self.human_index: int = 1
        self.active_index: int = self.human_index
        self.drag_state: DragState = DragState()
        self.card_tags: Dict[tuple[int, str], Card] = {}
        self.selected_card: Optional[Card] = None
        self.selected_player_idx: Optional[int] = None
        self.selected_tag: Optional[str] = None
        self.preview_window: Optional[tk.Toplevel] = None
        self.detail_window: Optional[tk.Toplevel] = None
        self.drop_zone_boxes: Dict[int, tuple[int, int, int, int]] = {}
        self.drop_zone_items: Dict[int, tuple[int, int]] = {}
        self.drop_zone_screen_bounds: Dict[int, tuple[int, int, int, int]] = {}

        self._build_layout()
        self._render_all()

    def _build_layout(self) -> None:
        control_frame = tk.Frame(self.root)
        control_frame.pack(side=tk.TOP, fill=tk.X)

        self.active_label = tk.Label(control_frame, text="Active player: You", font=("Arial", 12, "bold"))
        self.active_label.pack(side=tk.LEFT, padx=8, pady=4)

        tk.Button(control_frame, text="Draw Card", command=self.draw_card).pack(side=tk.LEFT, padx=4)
        tk.Button(control_frame, text="Play Selected", command=self.play_selected).pack(side=tk.LEFT, padx=4)
        tk.Button(control_frame, text="Play Queued Territory", command=self.play_queued_territory).pack(side=tk.LEFT, padx=4)
        tk.Button(control_frame, text="Pray with Gods", command=self.pray).pack(side=tk.LEFT, padx=4)
        tk.Button(control_frame, text="Resolve Stack", command=self.resolve_stack).pack(side=tk.LEFT, padx=4)
        tk.Button(control_frame, text="End Turn", command=self.end_turn).pack(side=tk.LEFT, padx=4)

        board_frame = tk.Frame(self.root)
        board_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # CPU (index 0) on top, human (index 1) on bottom for clarity
        self.player_frames = []
        self.resource_labels = []
        self.influence_labels = []
        self.battlefield_canvases = []
        self.hand_canvases = []

        for idx, player in enumerate(self.game.players):
            frame = tk.LabelFrame(board_frame, text=player.name)
            frame.pack(side=tk.TOP, fill=tk.X, padx=8, pady=6)
            self.player_frames.append(frame)

            info_frame = tk.Frame(frame)
            info_frame.pack(side=tk.TOP, fill=tk.X)
            resource_lbl = tk.Label(info_frame, text="Resources")
            resource_lbl.pack(side=tk.LEFT, padx=4)
            self.resource_labels.append(resource_lbl)

            influence_lbl = tk.Label(info_frame, text="Influence: 20")
            influence_lbl.pack(side=tk.LEFT, padx=4)
            self.influence_labels.append(influence_lbl)

            battlefield = tk.Canvas(frame, height=140, bg="#f3f3f3")
            battlefield.pack(side=tk.TOP, fill=tk.X, padx=4, pady=4)
            self.battlefield_canvases.append(battlefield)

            hand = tk.Canvas(frame, height=120, bg="#e8e8ff")
            hand.pack(side=tk.TOP, fill=tk.X, padx=4, pady=4)
            self.hand_canvases.append(hand)

        log_frame = tk.Frame(self.root)
        log_frame.pack(side=tk.BOTTOM, fill=tk.BOTH)
        tk.Label(log_frame, text="Action Log").pack(anchor="w")
        self.log_widget = tk.Text(log_frame, height=12, state=tk.DISABLED)
        self.log_widget.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

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
        self._draw_drop_zone(idx)
        for i, card in enumerate(player.battlefield):
            x = 10 + i * 130
            y = 10
            rect = canvas.create_rectangle(x, y, x + 120, y + 110, fill="#d9f7d9", outline="#4a7b4a")
            canvas.create_text(x + 60, y + 15, text=card.name, font=("Arial", 10, "bold"))
            canvas.create_text(x + 60, y + 40, text=card.text[:40] + ("..." if len(card.text) > 40 else ""), width=110)
            if isinstance(card, Cryptid):
                canvas.create_text(x + 60, y + 70, text=card.stats.describe(), fill="#1f4b99")
                canvas.create_text(x + 60, y + 95, text=f"Current HP: {card.current_health}", fill="#b03060")
            elif isinstance(card, GodCard):
                canvas.create_text(x + 60, y + 80, text=card.prayer_text or card.text, width=110)
            else:
                canvas.create_text(x + 60, y + 80, text=card.text, width=110)
            canvas.itemconfigure(rect, tags=(f"bf_{idx}_{i}",))

    def _draw_drop_zone(self, idx: int) -> None:
        canvas = self.battlefield_canvases[idx]
        canvas.update_idletasks()
        pad = 8
        width = max(canvas.winfo_width() - pad * 2, 160)
        height = max(canvas.winfo_height() - pad * 2, 110)
        x1, y1 = pad, pad
        x2, y2 = x1 + width, y1 + height
        rect_tag = f"drop_zone_{idx}_rect"
        label_tag = f"drop_zone_{idx}_label"
        if idx in self.drop_zone_items:
            rect_id, label_id = self.drop_zone_items[idx]
            canvas.delete(rect_id)
            canvas.delete(label_id)
        rect_id = canvas.create_rectangle(
            x1,
            y1,
            x2,
            y2,
            dash=(3, 2),
            outline="#7a8cff",
            fill="#eef2ff",
            tags=(rect_tag,),
        )
        label_id = canvas.create_text(
            (x1 + x2) / 2,
            y1 + 15,
            text="Drop to play",
            font=("Arial", 10, "bold"),
            fill="#1f4b99",
            tags=(label_tag,),
        )
        self.drop_zone_boxes[idx] = (x1, y1, x2, y2)
        self.drop_zone_items[idx] = (rect_id, label_id)

    def _refresh_drop_zone_bounds(self) -> None:
        for idx, canvas in enumerate(self.battlefield_canvases):
            if idx not in self.drop_zone_boxes:
                continue
            x1, y1, x2, y2 = self.drop_zone_boxes[idx]
            root_x, root_y = canvas.winfo_rootx(), canvas.winfo_rooty()
            self.drop_zone_screen_bounds[idx] = (root_x + x1, root_y + y1, root_x + x2, root_y + y2)

    def _highlight_drop_zone(self, active_idx: Optional[int]) -> None:
        for idx, items in self.drop_zone_items.items():
            rect_id, label_id = items
            canvas = self.battlefield_canvases[idx]
            is_active = active_idx == idx
            fill = "#d7ebff" if is_active else "#eef2ff"
            outline = "#2f6ad9" if is_active else "#7a8cff"
            text_color = "#0f2b5c" if is_active else "#1f4b99"
            canvas.itemconfigure(rect_id, fill=fill, outline=outline)
            canvas.itemconfigure(label_id, fill=text_color)

    def _create_drag_preview(self, card: Optional[Card]) -> None:
        if not card:
            return
        self._destroy_drag_preview()
        self.preview_window = tk.Toplevel(self.root)
        self.preview_window.overrideredirect(True)
        self.preview_window.attributes("-topmost", True)
        try:
            self.preview_window.attributes("-alpha", 0.9)
        except tk.TclError:
            pass
        canvas = tk.Canvas(self.preview_window, width=140, height=110, bg="", highlightthickness=0)
        canvas.pack()
        canvas.create_rectangle(5, 5, 135, 105, fill="#ffffff", outline="#6666aa", width=2)
        canvas.create_text(70, 20, text=card.name, font=("Arial", 10, "bold"))
        body_text = card.text
        if isinstance(card, Cryptid):
            body_text = f"{card.stats.describe()}\nHP: {card.current_health}\n{card.text}"
        elif isinstance(card, GodCard) and card.prayer_text:
            body_text = card.prayer_text
        canvas.create_text(70, 65, text=body_text, width=120)
        self._move_drag_preview(self.root.winfo_pointerx(), self.root.winfo_pointery())

    def _move_drag_preview(self, x_root: int, y_root: int) -> None:
        if not self.preview_window:
            return
        offset = 10
        self.preview_window.geometry(f"+{x_root + offset}+{y_root + offset}")

    def _destroy_drag_preview(self) -> None:
        if self.preview_window:
            self.preview_window.destroy()
            self.preview_window = None

    def _update_hover_target(self, x_root: int, y_root: int) -> None:
        target_idx: Optional[int] = None
        for idx in (self.human_index,):
            bounds = self.drop_zone_screen_bounds.get(idx)
            if not bounds:
                continue
            x1, y1, x2, y2 = bounds
            if x1 <= x_root <= x2 and y1 <= y_root <= y2:
                target_idx = idx
                break
        if target_idx != self.drag_state.hovered_target:
            self.drag_state.hovered_target = target_idx
            self._highlight_drop_zone(target_idx)

    def _render_hand(self, idx: int) -> None:
        canvas = self.hand_canvases[idx]
        canvas.delete("all")
        player = self.game.players[idx]
        self.card_tags = {key: value for key, value in self.card_tags.items() if key[0] != idx}
        for i, card in enumerate(player.hand):
            x = 10 + i * 130
            y = 10
            tag = f"hand_{idx}_{i}"
            rect = canvas.create_rectangle(x, y, x + 120, y + 100, fill="#ffffff", outline="#6666aa", tags=(tag,))
            text_tag = canvas.create_text(x + 60, y + 50, text=card.name, width=110, tags=(tag,))
            self.card_tags[(idx, tag)] = card
            canvas.tag_bind(tag, "<Button-1>", lambda e, t=tag, p=idx: self._select_card(p, t))
            canvas.tag_bind(tag, "<ButtonPress-1>", lambda e, t=tag, p=idx: self._start_drag(e, p, t))
            canvas.tag_bind(tag, "<B1-Motion>", lambda e, t=tag, p=idx: self._drag(e, p, t))
            canvas.tag_bind(tag, "<ButtonRelease-1>", lambda e, t=tag, p=idx: self._end_drag(e, p, t))
            canvas.itemconfig(text_tag, font=("Arial", 9, "bold"))

        if self.selected_player_idx == idx:
            if self.selected_card is None or self.selected_card not in player.hand:
                self._clear_selection()
            else:
                new_index = player.hand.index(self.selected_card)
                self.selected_tag = f"hand_{idx}_{new_index}"
                self._apply_selection_highlight()

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
        if self.drag_state.hovered_target is not None:
            if self._play_card(player_idx, card):
                self._clear_selection()
        self._highlight_drop_zone(None)
        self._destroy_drag_preview()
        self._render_hand(player_idx)
        self.drag_state = DragState()

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
            canvas.itemconfigure(self.selected_tag, outline="#ff8800", width=3)

    def _clear_selection(self) -> None:
        if self.selected_player_idx is not None and self.selected_tag:
            canvas = self.hand_canvases[self.selected_player_idx]
            if canvas.find_withtag(self.selected_tag):
                canvas.itemconfigure(self.selected_tag, outline="#6666aa", width=1)
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
            self.detail_window.destroy()
            self.detail_window = None

    def _show_card_details(self, card: Card) -> None:
        self._close_detail_window()
        self.detail_window = tk.Toplevel(self.root)
        self.detail_window.title(f"{card.name} Details")
        container = tk.Frame(self.detail_window, padx=10, pady=10)
        container.pack(fill=tk.BOTH, expand=True)

        tk.Label(container, text=card.name, font=("Arial", 14, "bold")).pack(anchor="w")
        type_cost = f"Type: {card.type.name.title()} | Cost: {self._format_cost(card)}"
        tk.Label(container, text=type_cost, font=("Arial", 10)).pack(anchor="w", pady=(2, 6))

        if card.faction:
            tk.Label(container, text=f"Faction: {card.faction}", font=("Arial", 10, "italic")).pack(anchor="w")
        if card.tags:
            tk.Label(container, text=f"Tags: {', '.join(card.tags)}", font=("Arial", 10)).pack(anchor="w")

        if card.text:
            tk.Label(
                container,
                text=card.text,
                wraplength=380,
                justify=tk.LEFT,
                font=("Arial", 10),
            ).pack(anchor="w", pady=(6, 6))

        if isinstance(card, TerritoryCard):
            yields = []
            if card.fear_yield:
                yields.append(f"{card.fear_yield} Fear")
            if card.belief_yield:
                yields.append(f"{card.belief_yield} Belief")
            yield_text = ", ".join(yields) if yields else "None"
            tk.Label(container, text=f"Yields: {yield_text}", font=("Arial", 10, "bold")).pack(anchor="w")

        if isinstance(card, Cryptid):
            tk.Label(container, text=f"Stats: {card.stats.describe()}", font=("Arial", 10, "bold")).pack(anchor="w")
            tk.Label(container, text=f"Current HP: {card.current_health}", font=("Arial", 10)).pack(anchor="w")
            if card.moves:
                moves_frame = tk.LabelFrame(container, text="Moves")
                moves_frame.pack(fill=tk.BOTH, expand=True, pady=(6, 4))
                for move in card.moves:
                    tk.Label(
                        moves_frame,
                        text=move.describe(),
                        wraplength=360,
                        justify=tk.LEFT,
                        anchor="w",
                    ).pack(anchor="w", padx=6, pady=2)
            if card.branches:
                branches_frame = tk.LabelFrame(container, text="Branches")
                branches_frame.pack(fill=tk.BOTH, expand=True, pady=(4, 4))
                for branch in card.branches:
                    tk.Label(
                        branches_frame,
                        text=f"{branch.name} — {branch.trigger}: {branch.effect_text}",
                        wraplength=360,
                        justify=tk.LEFT,
                        anchor="w",
                    ).pack(anchor="w", padx=6, pady=2)

        if isinstance(card, EventCard):
            impact = card.impact_text or card.text
            tk.Label(container, text=f"Impact: {impact}", wraplength=380, justify=tk.LEFT).pack(anchor="w")

        if isinstance(card, GodCard):
            if card.prayer_text:
                tk.Label(
                    container,
                    text=f"Prayer: {card.prayer_text}",
                    wraplength=380,
                    justify=tk.LEFT,
                ).pack(anchor="w")

        tk.Button(container, text="Close", command=self._close_detail_window).pack(anchor="e", pady=(10, 0))

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
