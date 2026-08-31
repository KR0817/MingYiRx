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
matplotlib.rcParams["svg.hashsalt"] = "mingyirx-network-v0.8"
os.environ.setdefault("SOURCE_DATE_EPOCH", "0")

import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle
import networkx as nx
import pandas as pd

import cnsplots as cns


COLORS = ("#B24745", "#3B6FB6", "#2F8F83")
LAYOUT_SEED = 20260901


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


def _selected_groups(
    sensitivity: pd.DataFrame, requested: list[str] | None
) -> list[str]:
    primary = sensitivity[sensitivity["primary_setting"].astype(str).eq("True")]
    available = primary["group"].astype(str).drop_duplicates().tolist()
    selected = requested or available
    unknown = sorted(set(selected) - set(available))
    if unknown:
        raise ValueError(f"Unknown groups: {unknown}")
    if not 1 <= len(selected) <= 3:
        raise ValueError("Select one to three groups with --groups")
    return selected


def _graph_layout(graph: nx.Graph) -> dict[str, tuple[float, float]]:
    if not graph:
        return {}
    components = sorted(
        nx.connected_components(graph), key=lambda component: (-len(component), min(component))
    )
    if len(components) == 1:
        positions = nx.spring_layout(
            graph,
            seed=LAYOUT_SEED,
            weight="cosine",
            iterations=500,
            k=1.35 / math.sqrt(graph.number_of_nodes()),
            scale=0.95,
        )
        return {
            node: (float(value[0]), float(value[1]))
            for node, value in positions.items()
        }

    def ordered_component(nodes: set[str]) -> nx.Graph:
        component_graph = graph.subgraph(nodes)
        ordered = nx.Graph()
        ordered.add_nodes_from(sorted(component_graph.nodes))
        for left, right in sorted(
            tuple(sorted((left, right))) for left, right in component_graph.edges
        ):
            ordered.add_edge(left, right, **component_graph[left][right])
        return ordered

    main_graph = ordered_component(components[0])
    positions = nx.spring_layout(
        main_graph,
        seed=LAYOUT_SEED,
        weight="cosine",
        iterations=500,
        k=1.35 / math.sqrt(main_graph.number_of_nodes()),
        scale=0.78,
        center=(-0.15, 0.0),
    )
    side_components = components[1:]
    side_y_values = [
        0.75 - 1.5 * index / max(1, len(side_components) - 1)
        for index in range(len(side_components))
    ]
    for index, (component, y_value) in enumerate(
        zip(side_components, side_y_values, strict=True), start=1
    ):
        if len(component) == 1:
            node = next(iter(component))
            positions[node] = (0.82, y_value)
            continue
        side_graph = ordered_component(component)
        positions.update(
            nx.spring_layout(
                side_graph,
                seed=LAYOUT_SEED + index,
                weight="cosine",
                iterations=300,
                scale=0.16,
                center=(0.82, y_value),
            )
        )
    return {node: (float(value[0]), float(value[1])) for node, value in positions.items()}


def _draw_networks(
    nodes: pd.DataFrame,
    edges: pd.DataFrame,
    sensitivity: pd.DataFrame,
    groups: list[str],
    output_dir: Path,
) -> None:
    primary = sensitivity[sensitivity["primary_setting"].astype(str).eq("True")]
    label_lookup = dict(zip(primary["group"], primary["group_label"], strict=True))

    multipanel = cns.multipanel(max_width=1800)
    axes = [
        multipanel.panel(
            chr(ord("A") + index),
            width=520,
            height=500,
            pad_left=12,
            pad_top=12,
            margin_right=28,
            margin_bottom=24,
        )
        for index in range(len(groups))
    ]

    for index, (group, ax) in enumerate(zip(groups, axes, strict=True)):
        group_nodes = nodes[nodes["group"].eq(group)].copy()
        group_edges = edges[edges["group"].eq(group)].copy()
        graph = nx.Graph()
        graph.add_nodes_from(group_nodes["item_name"].astype(str))
        for row in group_edges.itertuples(index=False):
            graph.add_edge(
                str(row.item_1),
                str(row.item_2),
                cosine=float(row.cosine_similarity),
            )
        if graph.number_of_nodes() == 0:
            ax.text(0.5, 0.5, "No reportable network", ha="center", va="center")
            ax.set_axis_off()
            continue

        group_positions = _graph_layout(graph)
        prevalence = dict(
            zip(group_nodes["item_name"], group_nodes["prevalence"], strict=True)
        )
        node_sizes = [300 + 850 * float(prevalence[node]) for node in graph.nodes]
        edge_widths = [
            0.8 + 4.5 * float(attributes["cosine"])
            for _, _, attributes in graph.edges(data=True)
        ]
        color = COLORS[index]
        nx.draw_networkx_edges(
            graph,
            group_positions,
            ax=ax,
            width=edge_widths,
            edge_color=color,
            alpha=0.28,
        )
        nx.draw_networkx_nodes(
            graph,
            group_positions,
            ax=ax,
            node_size=node_sizes,
            node_color=color,
            edgecolors="white",
            linewidths=1.2,
            alpha=0.92,
        )
        for node, (x_value, y_value) in group_positions.items():
            ax.text(
                x_value,
                y_value,
                node,
                ha="center",
                va="center",
                fontsize=10.5,
                fontweight="bold",
                fontproperties=CJK_FONT,
                bbox={
                    "facecolor": "white",
                    "edgecolor": "none",
                    "alpha": 0.74,
                    "pad": 0.7,
                },
            )
        summary = primary[primary["group"].eq(group)].iloc[0]
        ax.set_title(
            f"{label_lookup[group]}  |  n={int(summary['patients'])}; "
            f"nodes={graph.number_of_nodes()}; edges={graph.number_of_edges()}",
            loc="left",
            fontsize=13,
            fontweight="bold",
        )
        ax.set_axis_off()
        ax.set_xlim(-1.15, 1.15)
        ax.set_ylim(-1.15, 1.15)

    figure = plt.gcf()
    figure.text(
        0.5,
        0.012,
        "Deterministic layout per group; node size = first-prescription prevalence; edge width = cosine similarity",
        ha="center",
        va="bottom",
        fontsize=10,
        color="#444444",
    )
    cns.savefig(output_dir / "network_overview.svg")
    cns.savefig(output_dir / "network_overview.png")
    plt.close(figure)


def _draw_threshold_sensitivity(
    sensitivity: pd.DataFrame, groups: list[str], output_dir: Path
) -> None:
    primary = sensitivity[sensitivity["primary_setting"].astype(str).eq("True")]
    label_lookup = dict(zip(primary["group"], primary["group_label"], strict=True))
    multipanel = cns.multipanel(max_width=1800)
    axes = [
        multipanel.panel(
            chr(ord("A") + index),
            width=430,
            height=390,
            pad_left=18,
            pad_top=12,
            margin_right=48,
            margin_bottom=55,
        )
        for index in range(len(groups))
    ]
    image = None
    for group, ax in zip(groups, axes, strict=True):
        group_data = sensitivity[sensitivity["group"].eq(group)].copy()
        node_thresholds = sorted(group_data["node_prevalence_threshold"].unique())
        cosine_thresholds = sorted(group_data["edge_cosine_threshold"].unique())
        matrix = group_data.pivot(
            index="node_prevalence_threshold",
            columns="edge_cosine_threshold",
            values="edge_jaccard_vs_primary",
        ).reindex(index=node_thresholds, columns=cosine_thresholds)
        image = ax.imshow(matrix.to_numpy(dtype=float), vmin=0, vmax=1, cmap="Blues")
        for row_index, node_threshold in enumerate(node_thresholds):
            for column_index, cosine_threshold in enumerate(cosine_thresholds):
                value = matrix.iloc[row_index, column_index]
                text = "NA" if pd.isna(value) else f"{value:.2f}"
                color = "white" if not pd.isna(value) and value >= 0.58 else "#222222"
                ax.text(
                    column_index,
                    row_index,
                    text,
                    ha="center",
                    va="center",
                    fontsize=11,
                    fontweight="bold",
                    color=color,
                )
                primary_row = group_data[
                    group_data["node_prevalence_threshold"].eq(node_threshold)
                    & group_data["edge_cosine_threshold"].eq(cosine_threshold)
                    & group_data["primary_setting"].astype(str).eq("True")
                ]
                if not primary_row.empty:
                    ax.add_patch(
                        Rectangle(
                            (column_index - 0.5, row_index - 0.5),
                            1,
                            1,
                            fill=False,
                            edgecolor="#E69F00",
                            linewidth=3,
                        )
                    )
        ax.set_xticks(range(len(cosine_thresholds)), [f"{value:.2f}" for value in cosine_thresholds])
        ax.set_yticks(range(len(node_thresholds)), [f"{100 * value:.0f}%" for value in node_thresholds])
        ax.set_xlabel("Edge cosine threshold", fontsize=11)
        ax.set_ylabel("Node prevalence threshold", fontsize=11)
        ax.set_title(label_lookup[group], loc="left", fontsize=13, fontweight="bold")
        ax.tick_params(labelsize=10)

    figure = plt.gcf()
    if image is not None:
        colorbar = figure.colorbar(image, ax=axes, fraction=0.025, pad=0.025)
        colorbar.set_label("Edge-set Jaccard vs primary", fontsize=10)
        colorbar.ax.tick_params(labelsize=9)
    figure.text(
        0.5,
        0.012,
        "Orange border = primary setting; Jaccard measures edge membership, not clinical similarity",
        ha="center",
        va="bottom",
        fontsize=10,
        color="#444444",
    )
    cns.savefig(output_dir / "network_threshold_sensitivity.svg")
    cns.savefig(output_dir / "network_threshold_sensitivity.png")
    plt.close(figure)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Plot privacy-screened MingYiRx recurrent-item networks."
    )
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--groups", nargs="+")
    args = parser.parse_args()

    nodes = _read_table(
        args.input_dir / "network_nodes.csv",
        {"group", "group_label", "item_name", "prevalence"},
    )
    edges = _read_table(
        args.input_dir / "network_edges.csv",
        {"group", "item_1", "item_2", "cosine_similarity"},
    )
    sensitivity = _read_table(
        args.input_dir / "network_threshold_sensitivity.csv",
        {
            "group",
            "group_label",
            "patients",
            "node_prevalence_threshold",
            "edge_cosine_threshold",
            "edge_jaccard_vs_primary",
            "primary_setting",
        },
    )
    groups = _selected_groups(sensitivity, args.groups)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    with cns.settings.context(
        title_fontsize=13,
        savefig_dpi=300,
        savefig_transparent=False,
        savefig_pad_inches=0.03,
        font_sans_serif=("Microsoft YaHei", "Arial", "DejaVu Sans"),
        panel_label_fontname="Microsoft YaHei",
    ):
        _draw_networks(nodes, edges, sensitivity, groups, args.output_dir)
        _draw_threshold_sensitivity(sensitivity, groups, args.output_dir)

    figure_paths = sorted(args.output_dir.glob("network_*.png")) + sorted(
        args.output_dir.glob("network_*.svg")
    )
    for path in figure_paths:
        if path.stat().st_size == 0:
            raise RuntimeError(f"Empty figure: {path}")
        print(path)

    input_paths = [
        args.input_dir / "network_nodes.csv",
        args.input_dir / "network_edges.csv",
        args.input_dir / "network_threshold_sensitivity.csv",
    ]
    manifest = {
        "groups": groups,
        "layout_seed": LAYOUT_SEED,
        "inputs": {path.name: _sha256(path) for path in input_paths},
        "software": {
            "python": platform.python_version(),
            "cnsplots": cns.__version__,
            "matplotlib": matplotlib.__version__,
            "networkx": nx.__version__,
            "pandas": pd.__version__,
        },
        "artifacts": {path.name: _sha256(path) for path in figure_paths},
    }
    manifest_path = args.output_dir / "network_figure_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(manifest_path)


if __name__ == "__main__":
    main()
