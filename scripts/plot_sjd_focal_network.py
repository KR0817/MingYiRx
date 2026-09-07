from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "mingyirx-sjd-focal-network-v1"
os.environ.setdefault("SOURCE_DATE_EPOCH", "0")

import matplotlib.pyplot as plt
from matplotlib import font_manager
import networkx as nx
import pandas as pd

import cnsplots as cns


FOCAL_COLOR = "#C9473D"
BASE_COLOR = "#52799B"
EDGE_COLOR = "#547E94"
TEXT_COLOR = "#24313A"


def _cjk_font() -> font_manager.FontProperties:
    for family in ("Microsoft YaHei", "SimHei", "Noto Sans CJK SC"):
        try:
            path = font_manager.findfont(family, fallback_to_default=False)
        except ValueError:
            continue
        return font_manager.FontProperties(fname=path)
    raise RuntimeError("A CJK font is required to render item names")


CJK_FONT = _cjk_font()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_table(path: Path, required: set[str]) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(path)
    data = pd.read_csv(path)
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"{path.name} is missing columns: {sorted(missing)}")
    return data


def _prepare_data(
    input_dir: Path,
    group: str,
    focal_item: str,
    top_n: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, int, str]:
    prevalence = _read_table(
        input_dir / "first_prescription_item_prevalence.csv",
        {
            "group",
            "item_name",
            "exposed_patients",
            "group_patients",
            "prevalence",
        },
    )
    nodes = _read_table(
        input_dir / "network_nodes.csv",
        {
            "group",
            "group_label",
            "item_name",
            "exposed_patients",
            "prevalence",
        },
    )
    edges = _read_table(
        input_dir / "network_edges.csv",
        {
            "group",
            "item_1",
            "item_2",
            "cooccurrence_patients",
            "cosine_similarity",
        },
    )

    group_prevalence = prevalence[prevalence["group"].eq(group)].copy()
    if group_prevalence.empty:
        raise ValueError(f"Unknown or empty group: {group}")
    group_prevalence = group_prevalence.sort_values(
        ["prevalence", "item_name"], ascending=[False, True]
    )
    focal_prevalence = group_prevalence[
        group_prevalence["item_name"].eq(focal_item)
    ]
    if focal_prevalence.empty:
        raise ValueError(f"Focal item is not reportable in {group}: {focal_item}")

    top = group_prevalence.head(top_n).copy()
    if focal_item not in set(top["item_name"]):
        top = pd.concat([top.iloc[:-1], focal_prevalence], ignore_index=True)
        top = top.sort_values(["prevalence", "item_name"], ascending=[False, True])
    top["prevalence_pct"] = 100 * top["prevalence"].astype(float)

    group_nodes = nodes[nodes["group"].eq(group)].copy()
    group_edges = edges[edges["group"].eq(group)].copy()
    focal_edges = group_edges[
        group_edges["item_1"].eq(focal_item)
        | group_edges["item_2"].eq(focal_item)
    ].copy()
    if focal_edges.empty:
        raise ValueError(f"Focal item has no reportable network edge: {focal_item}")
    focal_edges["neighbor"] = focal_edges.apply(
        lambda row: row["item_2"] if row["item_1"] == focal_item else row["item_1"],
        axis=1,
    )
    focal_edges = focal_edges.sort_values(
        ["cosine_similarity", "neighbor"], ascending=[False, True]
    )
    included = {focal_item, *focal_edges["neighbor"].astype(str)}
    focal_nodes = group_nodes[group_nodes["item_name"].isin(included)].copy()
    missing_nodes = included.difference(focal_nodes["item_name"].astype(str))
    if missing_nodes:
        raise ValueError(f"Network nodes are missing: {sorted(missing_nodes)}")

    group_patients = int(focal_prevalence.iloc[0]["group_patients"])
    label_rows = group_nodes["group_label"].dropna().astype(str).drop_duplicates()
    group_label = label_rows.iloc[0] if not label_rows.empty else group
    return top, focal_nodes, focal_edges, group_patients, group_label


def _draw_frequency_panel(
    ax: plt.Axes,
    top: pd.DataFrame,
    focal_item: str,
    group_patients: int,
) -> None:
    order = top["item_name"].astype(str).tolist()
    cns.lollipopplot(
        data=top,
        x="prevalence_pct",
        y="item_name",
        order=order,
        color="#9AA9B2",
        markersize=34,
        linewidth=2.0,
        ax=ax,
    )
    ax.invert_yaxis()
    tick_positions = {
        label.get_text(): tick
        for tick, label in zip(ax.get_yticks(), ax.get_yticklabels(), strict=True)
    }
    focal_row = top[top["item_name"].eq(focal_item)].iloc[0]
    focal_y = tick_positions[focal_item]
    focal_value = float(focal_row["prevalence_pct"])
    ax.hlines(focal_y, 0, focal_value, color=FOCAL_COLOR, linewidth=3.0, zorder=3)
    ax.scatter(
        [focal_value],
        [focal_y],
        s=74,
        color=FOCAL_COLOR,
        edgecolor="white",
        linewidth=1.1,
        zorder=4,
    )

    for row in top.itertuples(index=False):
        y_value = tick_positions[str(row.item_name)]
        color = FOCAL_COLOR if str(row.item_name) == focal_item else TEXT_COLOR
        ax.text(
            float(row.prevalence_pct) + 1.25,
            y_value,
            f"{float(row.prevalence_pct):.1f}%",
            ha="left",
            va="center",
            fontsize=9.5,
            fontweight="bold" if str(row.item_name) == focal_item else "normal",
            color=color,
        )

    for label in ax.get_yticklabels():
        label.set_fontproperties(CJK_FONT)
        label.set_fontsize(10.5)
        if label.get_text() == focal_item:
            label.set_color(FOCAL_COLOR)
            label.set_fontweight("bold")
    upper = max(100.0, float(top["prevalence_pct"].max()) + 10.0)
    ax.set_xlim(0, upper)
    ax.set_xlabel("Patients with item at first prescription (%)", fontsize=10.5)
    ax.set_ylabel("")
    ax.set_title(
        f"High-frequency items | n={group_patients}",
        loc="left",
        fontsize=13,
        fontweight="bold",
    )
    ax.grid(axis="x", color="#DCE3E7", linewidth=0.8, alpha=0.8)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.tick_params(axis="x", labelsize=9.5)


def _radial_positions(
    focal_item: str, focal_edges: pd.DataFrame
) -> dict[str, tuple[float, float]]:
    positions = {focal_item: (0.0, 0.0)}
    neighbors = focal_edges["neighbor"].astype(str).tolist()
    for index, neighbor in enumerate(neighbors):
        angle = math.pi / 2 - 2 * math.pi * index / len(neighbors)
        positions[neighbor] = (1.02 * math.cos(angle), 0.86 * math.sin(angle))
    return positions


def _draw_network_panel(
    ax: plt.Axes,
    nodes: pd.DataFrame,
    focal_edges: pd.DataFrame,
    focal_item: str,
    group_label: str,
) -> None:
    graph = nx.Graph()
    for row in nodes.itertuples(index=False):
        graph.add_node(
            str(row.item_name),
            prevalence=float(row.prevalence),
            exposed=int(row.exposed_patients),
        )
    for row in focal_edges.itertuples(index=False):
        graph.add_edge(
            focal_item,
            str(row.neighbor),
            cosine=float(row.cosine_similarity),
            cooccurrence=int(row.cooccurrence_patients),
        )

    positions = _radial_positions(focal_item, focal_edges)
    edges = list(graph.edges(data=True))
    nx.draw_networkx_edges(
        graph,
        positions,
        ax=ax,
        width=[1.0 + 7.0 * edge[2]["cosine"] for edge in edges],
        edge_color=EDGE_COLOR,
        alpha=0.36,
    )
    node_order = list(graph.nodes)
    node_sizes = [
        3800 if node == focal_item else 650 + 1200 * graph.nodes[node]["prevalence"]
        for node in node_order
    ]
    node_colors = [FOCAL_COLOR if node == focal_item else BASE_COLOR for node in node_order]
    nx.draw_networkx_nodes(
        graph,
        positions,
        nodelist=node_order,
        node_size=node_sizes,
        node_color=node_colors,
        edgecolors="white",
        linewidths=1.8,
        alpha=0.96,
        ax=ax,
    )

    for node, (x_value, y_value) in positions.items():
        prevalence = 100 * float(graph.nodes[node]["prevalence"])
        if node == focal_item:
            ax.text(
                x_value,
                y_value,
                f"{node}\n{prevalence:.1f}%",
                ha="center",
                va="center",
                fontsize=12.5,
                fontweight="bold",
                fontproperties=CJK_FONT,
                color="white",
                zorder=4,
            )
            continue
        ax.text(
            x_value,
            y_value,
            f"{prevalence:.1f}%",
            ha="center",
            va="center",
            fontsize=9.5,
            fontweight="bold",
            color="white",
            zorder=4,
        )
        label_scale = 1.13
        label_x = label_scale * x_value
        label_y = label_scale * y_value
        horizontal_alignment = (
            "left" if x_value > 0.2 else "right" if x_value < -0.2 else "center"
        )
        vertical_alignment = (
            "bottom" if y_value > 0.2 else "top" if y_value < -0.2 else "center"
        )
        ax.text(
            label_x,
            label_y,
            node,
            ha=horizontal_alignment,
            va=vertical_alignment,
            fontsize=10.5,
            fontweight="bold",
            fontproperties=CJK_FONT,
            color=TEXT_COLOR,
            zorder=5,
        )

    for left, right, attributes in edges:
        x_value = 0.48 * (positions[left][0] + positions[right][0])
        y_value = 0.48 * (positions[left][1] + positions[right][1])
        ax.text(
            x_value,
            y_value,
            f"n={attributes['cooccurrence']}",
            ha="center",
            va="center",
            fontsize=8.5,
            color=TEXT_COLOR,
            bbox={
                "facecolor": "white",
                "edgecolor": "none",
                "alpha": 0.88,
                "pad": 0.6,
            },
            zorder=5,
        )

    ax.set_title(
        "Core co-prescription network",
        loc="left",
        fontsize=13,
        fontweight="bold",
        y=1.055,
    )
    ax.text(
        0.0,
        1.005,
        f"Focal item: {focal_item} | {group_label}; node = prevalence; edge = cosine similarity",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=9.5,
        fontproperties=CJK_FONT,
        color="#59666E",
    )
    ax.set_xlim(-1.28, 1.28)
    ax.set_ylim(-1.08, 1.08)
    ax.set_aspect("equal")
    ax.set_axis_off()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plot a focal-item Sjogren disease frequency and core-network figure."
    )
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--group", default="sjd_strict")
    parser.add_argument("--focal-item", required=True)
    parser.add_argument("--top-n", type=int, default=15)
    parser.add_argument("--network-only", action="store_true")
    args = parser.parse_args()
    if args.top_n < 5:
        raise ValueError("--top-n must be at least 5")

    top, nodes, edges, patients, group_label = _prepare_data(
        args.input_dir, args.group, args.focal_item, args.top_n
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)

    with cns.settings.context(
        title_fontsize=13,
        savefig_dpi=300,
        savefig_transparent=False,
        savefig_pad_inches=0.03,
        font_sans_serif=("Microsoft YaHei", "Arial", "DejaVu Sans"),
        panel_label_fontname="Arial",
    ):
        if args.network_only:
            cns.figure(width=760, height=620)
            figure = plt.gcf()
            ax_network = plt.gca()
            _draw_network_panel(
                ax_network, nodes, edges, args.focal_item, group_label
            )
            figure.subplots_adjust(left=0.04, right=0.96, top=0.86, bottom=0.10)
            output_stem = args.output_dir / "sjd_focal_item_core_network"
            manifest_name = "sjd_focal_item_core_network_manifest.json"
        else:
            multipanel = cns.multipanel(max_width=1240)
            ax_frequency = multipanel.panel(
                "A",
                width=470,
                height=540,
                pad_left=18,
                pad_top=14,
                margin_right=30,
                margin_bottom=42,
            )
            ax_network = multipanel.panel(
                "B",
                width=600,
                height=540,
                pad_left=12,
                pad_top=14,
                margin_right=18,
                margin_bottom=42,
            )
            _draw_frequency_panel(ax_frequency, top, args.focal_item, patients)
            _draw_network_panel(
                ax_network, nodes, edges, args.focal_item, group_label
            )
            figure = plt.gcf()
            output_stem = args.output_dir / "sjd_focal_item_frequency_network"
            manifest_name = "sjd_focal_item_figure_manifest.json"
        figure.text(
            0.5,
            0.008,
            "Recorded first-prescription co-occurrence; descriptive association, not efficacy or a treatment recommendation",
            ha="center",
            va="bottom",
            fontsize=9.5,
            color="#59666E",
        )
        figure_paths = [output_stem.with_suffix(suffix) for suffix in (".svg", ".png")]
        for path in figure_paths:
            cns.savefig(path)
        plt.close(figure)

    input_paths = [
        args.input_dir / "first_prescription_item_prevalence.csv",
        args.input_dir / "network_nodes.csv",
        args.input_dir / "network_edges.csv",
    ]
    manifest = {
        "group": args.group,
        "group_label": group_label,
        "group_patients": patients,
        "focal_item": args.focal_item,
        "top_n": args.top_n,
        "focal_edges": len(edges),
        "layout": "network_only" if args.network_only else "frequency_and_network",
        "inputs": {path.name: _sha256(path) for path in input_paths},
        "software": {
            "python": platform.python_version(),
            "cnsplots": cns.__version__,
            "matplotlib": matplotlib.__version__,
            "networkx": nx.__version__,
            "pandas": pd.__version__,
        },
        "artifacts": {path.name: _sha256(path) for path in figure_paths},
        "interpretation": "Descriptive first-prescription co-occurrence only.",
    }
    manifest_path = args.output_dir / manifest_name
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    for path in [*figure_paths, manifest_path]:
        if path.stat().st_size == 0:
            raise RuntimeError(f"Empty artifact: {path}")
        print(path)


if __name__ == "__main__":
    main()
