#!/usr/bin/env python3
"""Desktop UI: field canvas, season controls, auto-play, replant-from-seed (like demo)."""

from __future__ import annotations

import random
import tkinter as tk
from tkinter import scrolledtext, ttk

from sim import (
    FieldPlot,
    Orchard,
    Seed,
    current_lifecycle_stage,
    default_phenotype_rules,
    random_plots_soil,
    species_by_id,
    stage_label,
)
from sim.lifecycle import LifecycleStage


def _plant_summary(plot: FieldPlot, rules) -> str:
    p = plot.plant
    if p is None:
        return "Fallow"
    scion_name = p.scion_species.common_name
    stock_name = p.rootstock_species.common_name
    life = stage_label(p)
    t = p.expressed_traits(rules)
    morph = ", ".join(f"{k}={t[k]}" for k in ("leaf", "shaft", "root_spread") if k in t)
    return f"{scion_name} on {stock_name}\nStage: {life}\n{morph}"


def _patch_fill(plot: FieldPlot) -> str:
    """Soil-ish RGB from water, nutrients, organic matter."""
    s = plot.soil
    r = int(70 + 110 * s.organic_matter)
    g = int(55 + 150 * s.nutrient_index)
    b = int(35 + 130 * s.water_saturation)
    return f"#{max(0, min(255, r)):02x}{max(0, min(255, g)):02x}{max(0, min(255, b)):02x}"


def _patch_outline(plot: FieldPlot) -> tuple[int, int]:
    """Outline width and color by lifecycle stage."""
    p = plot.plant
    if p is None:
        return 3, "#7f8c8d"
    st = current_lifecycle_stage(p)
    if st is LifecycleStage.PRODUCTIVE:
        return 4, "#c0392b"
    if st is LifecycleStage.FLOWERING:
        return 3, "#e67e22"
    if st in (
        LifecycleStage.GERMINATION,
        LifecycleStage.SEEDLING,
        LifecycleStage.GRAFT_ESTABLISHING,
    ):
        return 3, "#3498db"
    return 3, "#229954"  # vegetative


class RootstockGUI(tk.Tk):
    # Match demo.py: replot plot 2 from seed only while global season counter stays below this.
    _REPLANT_WHILE_SEASON_LT = 6

    def __init__(self) -> None:
        super().__init__()
        self.title("Rootstock — field & seasons")
        self.minsize(760, 600)
        self.rules = default_phenotype_rules()
        self.rng = random.Random(42)
        self.pear_root = species_by_id()["pyrus_communis"]
        self.plot_widgets: list[dict[str, ttk.Widget]] = []
        self.timeline_canvases: list[tk.Canvas] = []
        self.all_seeds: list[Seed] = []
        self.field_canvas: tk.Canvas | None = None
        self._autoplay_after_id: str | None = None

        self.autoplay_var = tk.BooleanVar(value=False)
        self.replant_var = tk.BooleanVar(value=True)
        self.speed_ms = tk.DoubleVar(value=650.0)

        self._build_orchard()
        self._build_ui()
        self.refresh_all()

    def _build_orchard(self) -> None:
        self.all_seeds = []
        soils = random_plots_soil(3, self.rng)
        self.plots = [FieldPlot(soil=s) for s in soils]
        self.plots[0].plant_graft_from_breed("apple_spur_type", self.pear_root)
        self.plots[1].plant_graft_from_breed("apple_standard", self.pear_root)
        self.plots[2].plant_graft_from_breed("apple_standard", self.pear_root)
        self.orchard = Orchard(plots=self.plots)

    def _pollen_map(self):
        if self.plots[1].plant:
            return {0: self.plots[1].plant.scion_genome}
        return None

    def _build_ui(self) -> None:
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")

        header = ttk.Frame(self, padding=8)
        header.pack(fill=tk.X)

        ttk.Label(header, text="Season", font=("Segoe UI", 10)).pack(side=tk.LEFT)
        self.season_var = tk.StringVar(value="0")
        ttk.Label(
            header,
            textvariable=self.season_var,
            font=("Segoe UI", 22, "bold"),
            width=4,
        ).pack(side=tk.LEFT, padx=(6, 12))

        ttk.Button(header, text="Advance 1", command=self.advance_one).pack(side=tk.LEFT, padx=2)
        ttk.Button(header, text="Advance 5", command=self.advance_five).pack(side=tk.LEFT, padx=2)
        ttk.Button(header, text="Reset", command=self.reset_sim).pack(side=tk.LEFT, padx=8)

        ctrl = ttk.Frame(self, padding=(8, 0, 8, 4))
        ctrl.pack(fill=tk.X)

        ttk.Checkbutton(
            ctrl,
            text="Auto-play",
            variable=self.autoplay_var,
            command=self._on_autoplay_toggle,
        ).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Label(ctrl, text="Speed (delay ms)").pack(side=tk.LEFT)
        sp = ttk.Scale(
            ctrl,
            from_=200,
            to=2200,
            variable=self.speed_ms,
            orient=tk.HORIZONTAL,
            length=200,
            command=lambda _v: None,
        )
        sp.pack(side=tk.LEFT, padx=4)
        self.speed_label = ttk.Label(ctrl, text="650 ms", width=10)
        self.speed_label.pack(side=tk.LEFT, padx=4)
        sp.configure(command=self._on_speed_moved)
        self._on_speed_moved("")

        ttk.Checkbutton(
            ctrl,
            text="Replant plot 2 from random seed (demo rule: while season < 6)",
            variable=self.replant_var,
        ).pack(side=tk.LEFT, padx=(16, 0))

        field_fr = ttk.LabelFrame(
            self,
            text="Field — soil RGB ≈ organic / nutrients / water; border = lifecycle (blue early, green veg, orange flowering, red productive)",
            padding=6,
        )
        field_fr.pack(fill=tk.X, padx=8, pady=4)
        self.field_canvas = tk.Canvas(
            field_fr,
            height=168,
            highlightthickness=1,
            highlightbackground="#bdc3c7",
            bg="#dfe6e9",
        )
        self.field_canvas.pack(fill=tk.BOTH, expand=True)
        self.field_canvas.bind("<Configure>", self._on_field_resize)

        tl_fr = ttk.LabelFrame(self, text="Cycle strip (one block per season)", padding=6)
        tl_fr.pack(fill=tk.X, padx=8, pady=(0, 4))
        inner = ttk.Frame(tl_fr)
        inner.pack()
        for i in range(36):
            c = tk.Canvas(
                inner,
                width=12,
                height=18,
                highlightthickness=0,
                bg="#f0f0f0",
            )
            r, col = divmod(i, 18)
            c.grid(row=r, column=col, padx=1, pady=1)
            self.timeline_canvases.append(c)

        plots_fr = ttk.Frame(self, padding=8)
        plots_fr.pack(fill=tk.BOTH, expand=True)
        for i in range(3):
            self._build_plot_card(plots_fr, i)

        log_fr = ttk.LabelFrame(self, text="Season log", padding=6)
        log_fr.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        self.log = scrolledtext.ScrolledText(log_fr, height=7, wrap=tk.WORD, font=("Consolas", 9))
        self.log.pack(fill=tk.BOTH, expand=True)

    def _on_speed_moved(self, _v: str) -> None:
        v = int(round(self.speed_ms.get()))
        self.speed_label.configure(text=f"{v} ms")
        if self.autoplay_var.get():
            self._schedule_autoplay()

    def _on_autoplay_toggle(self) -> None:
        if self.autoplay_var.get():
            self._schedule_autoplay()
        else:
            self._cancel_autoplay()

    def _cancel_autoplay(self) -> None:
        if self._autoplay_after_id is not None:
            self.after_cancel(self._autoplay_after_id)
            self._autoplay_after_id = None

    def _schedule_autoplay(self) -> None:
        self._cancel_autoplay()
        delay = max(50, int(round(self.speed_ms.get())))
        self._autoplay_after_id = self.after(delay, self._tick_autoplay)

    def _tick_autoplay(self) -> None:
        self._autoplay_after_id = None
        if not self.autoplay_var.get():
            return
        self.advance_one()
        if self.autoplay_var.get():
            delay = max(50, int(round(self.speed_ms.get())))
            self._autoplay_after_id = self.after(delay, self._tick_autoplay)

    def _on_field_resize(self, _event: tk.Event | None = None) -> None:
        self._draw_field()

    def _draw_field(self) -> None:
        c = self.field_canvas
        if c is None:
            return
        c.delete("field")
        w = max(c.winfo_width(), 3)
        h = max(c.winfo_height(), 3)
        pad = 10
        gap = 8
        n = len(self.plots)
        inner_w = w - 2 * pad
        cell = (inner_w - gap * (n - 1)) // n
        y0, y1 = pad, h - pad
        for i, plot in enumerate(self.plots):
            x0 = pad + i * (cell + gap)
            x1 = x0 + cell
            fill = _patch_fill(plot)
            ow, oc = _patch_outline(plot)
            c.create_rectangle(
                x0,
                y0,
                x1,
                y1,
                fill=fill,
                outline=oc,
                width=ow,
                tags="field",
            )
            c.create_text(
                (x0 + x1) // 2,
                (y0 + y1) // 2,
                text=f"Plot {i}",
                fill="#2c3e50",
                font=("Segoe UI", 11, "bold"),
                tags="field",
            )
            p = plot.plant
            sub = "Fallow" if p is None else stage_label(p)
            c.create_text(
                (x0 + x1) // 2,
                y1 - 14,
                text=sub,
                fill="#34495e",
                font=("Segoe UI", 9),
                tags="field",
            )

    def _build_plot_card(self, parent: ttk.Frame, index: int) -> None:
        lf = ttk.LabelFrame(parent, text=f"Plot {index}", padding=8)
        lf.pack(fill=tk.X, pady=4)

        soil_fr = ttk.Frame(lf)
        soil_fr.pack(fill=tk.X)

        def bar_row(row: int, label: str) -> ttk.Progressbar:
            ttk.Label(soil_fr, text=label, width=12).grid(row=row, column=0, sticky=tk.W)
            pb = ttk.Progressbar(soil_fr, length=220, maximum=100, mode="determinate")
            pb.grid(row=row, column=1, sticky=tk.EW, padx=6, pady=2)
            return pb

        soil_fr.columnconfigure(1, weight=1)
        w_bar = bar_row(0, "Water")
        n_bar = bar_row(1, "Nutrients")
        o_bar = bar_row(2, "Organic matter")
        ph_lbl = ttk.Label(soil_fr, text="pH —")
        ph_lbl.grid(row=3, column=1, sticky=tk.W, padx=6)
        drain_lbl = ttk.Label(soil_fr, text="Drainage / compaction —")
        drain_lbl.grid(row=4, column=1, sticky=tk.W, padx=6)

        plant_lbl = ttk.Label(lf, text="", justify=tk.LEFT)
        plant_lbl.pack(anchor=tk.W, pady=(8, 0))

        self.plot_widgets.append(
            {
                "water": w_bar,
                "nutrients": n_bar,
                "om": o_bar,
                "ph": ph_lbl,
                "drain": drain_lbl,
                "plant": plant_lbl,
            }
        )

    def _paint_timeline(self) -> None:
        done = "#27ae60"
        idle = "#ecf0f1"
        filled = min(self.orchard.season, len(self.timeline_canvases))
        for i, cv in enumerate(self.timeline_canvases):
            cv.delete("all")
            fill = done if i < filled else idle
            cv.create_rectangle(1, 1, 11, 17, fill=fill, outline="#bdc3c7")

    def refresh_all(self) -> None:
        self.season_var.set(str(self.orchard.season))
        self._paint_timeline()
        self._draw_field()
        for i, plot in enumerate(self.plots):
            w = self.plot_widgets[i]
            s = plot.soil
            w["water"]["value"] = round(s.water_saturation * 100)
            w["nutrients"]["value"] = round(s.nutrient_index * 100)
            w["om"]["value"] = round(s.organic_matter * 100)
            w["ph"].configure(text=f"pH {s.ph:.2f}")
            w["drain"].configure(
                text=f"Drainage {s.drainage:.2f} · Compaction {s.compaction:.2f}"
            )
            w["plant"].configure(text=_plant_summary(plot, self.rules))

    def advance_one(self) -> None:
        harvests = self.orchard.run_season(
            self.rng,
            self.rules,
            pollen_by_plot=self._pollen_map(),
            seeds_per_harvest=2,
            mutation_rate=0.04,
        )
        for h in harvests:
            self.all_seeds.extend(h.seeds)

        lines = [f"Season {self.orchard.season} ended.  Seed bank: {len(self.all_seeds)}"]
        if not harvests:
            lines.append("No harvests (plants still immature or fallow).")
        for h in harvests:
            morph = {
                k: h.traits_snapshot[k]
                for k in ("leaf", "shaft", "root_spread")
                if k in h.traits_snapshot
            }
            lines.append(f"  {h.species_id}: seeds={len(h.seeds)} morph={morph}")

        if (
            self.replant_var.get()
            and self.all_seeds
            and self.orchard.season < self._REPLANT_WHILE_SEASON_LT
        ):
            pick = self.rng.choice(self.all_seeds)
            self.plots[2].plant = None
            self.plots[2].plant_seed(pick, self.pear_root, self.rng)
            sugar = pick.genome.loci.get("sugar")
            lines.append(f"  Replanted plot 2 from seed (sugar locus {sugar}).")

        self._append_log("\n".join(lines) + "\n")
        self.refresh_all()

    def advance_five(self) -> None:
        for _ in range(5):
            self.advance_one()

    def reset_sim(self) -> None:
        self._cancel_autoplay()
        self.autoplay_var.set(False)
        self.rng = random.Random(42)
        self._build_orchard()
        self.log.delete("1.0", tk.END)
        self._append_log("Simulation reset.\n")
        self.refresh_all()

    def _append_log(self, text: str) -> None:
        self.log.insert(tk.END, text)
        self.log.see(tk.END)

    def destroy(self) -> None:
        self._cancel_autoplay()
        super().destroy()


def main() -> None:
    app = RootstockGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
