# -*- coding: utf-8 -*-
"""纵向方框图模板 —— 生成真图(不再用 ASCII 手拼)。

默认生成题 1-3(炉温系统);换题时用命令行参数:

    python block_diagram.py --nodes '比较点|$\\oplus$   $\\ominus$;放大器;电动机 M;减速器;输出轴与发射架' \
        --feedback '电位器 P2' --out autocontrol-1-4-block \
        --input '$\\theta_1$' --output '$\\theta_2$' --feedback-label '$u_2$'

参数说明:
    --nodes           分号分隔的环节名;框内换行用 | 表示
    --feedback        反馈环节名;不需要反馈通道时不传(传空)
    --out             输出文件名(只写主干,**只用 ASCII**)
    --input/--output  输入、输出标注(LaTeX)
    --feedback-label  反馈信号标注(LaTeX)

要点:
- 中文字体走 Microsoft YaHei;公式符号一律走 mathtext(避免缺字形方块)。
- 比较点用 $\\oplus$ / $\\ominus$ 标极性,反馈线从下方绕回比较点右侧。
- 输出 PNG + SVG 到图床目录,再用 ![](http://127.0.0.1:8765/<out>.png) 内联。
"""
import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

OUT_DIR = os.environ.get(
    "DSH_FIGS_DIR",
    os.path.join(os.environ.get("TEMP") or os.path.expanduser("~"), "dsh-figs"),
)

DEFAULT_NODES = [
    "比较点\n$\\oplus$   $\\ominus$",
    "电压放大",
    "功率放大",
    "电动机 M",
    "减速器",
    "调压器",
    "电炉",
]


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--nodes", default=None, help="分号分隔的环节名,| 表示框内换行")
    p.add_argument("--feedback", default="热电偶")
    p.add_argument("--out", default="autocontrol-1-3-block")
    p.add_argument("--input", dest="in_label", default="$u_g$")
    p.add_argument("--output", dest="out_label", default="$T$(炉温)")
    p.add_argument("--feedback-label", dest="fb_label", default="$u_f$")
    return p.parse_args()


def main():
    a = parse_args()
    nodes = ([n.replace("|", "\n") for n in a.nodes.split(";")]
             if a.nodes else DEFAULT_NODES)
    fb_node = a.feedback or None

    n = len(nodes)
    bw, bh, gap = 3.2, 0.95, 0.72
    cx = 0.0
    ys = [-i * (bh + gap) for i in range(n)]
    fb_y = ys[-1] - (bh + gap) - 0.1 if fb_node else None

    right_x = cx + bw / 2 + 2.3
    left_x = cx - bw / 2 - 2.1
    top = ys[0] + bh / 2 + 1.3
    bottom = (fb_y - bh / 2 - 0.6) if fb_node else (ys[-1] - bh / 2 - 0.6)

    fig, ax = plt.subplots(figsize=(5.8, (top - bottom) * 0.60))
    ax.set_xlim(left_x - 1.6, right_x + 1.8)
    ax.set_ylim(bottom, top)
    ax.axis("off")

    def box(x, y, w, h, text, fs=11):
        ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h,
                                    boxstyle="round,pad=0.02,rounding_size=0.1",
                                    linewidth=1.4, edgecolor="black",
                                    facecolor="#f7f9fc", zorder=3))
        ax.text(x, y, text, ha="center", va="center", fontsize=fs, zorder=4)

    def arrow(x1, y1, x2, y2):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                     mutation_scale=13, linewidth=1.3,
                                     color="black", zorder=2))

    def seg(x1, y1, x2, y2):
        ax.plot([x1, x2], [y1, y2], color="black", linewidth=1.3, zorder=2)

    for i, name in enumerate(nodes):
        box(cx, ys[i], bw, bh, name)
    for i in range(n - 1):
        arrow(cx, ys[i] - bh / 2, cx, ys[i + 1] + bh / 2)

    arrow(left_x, ys[0], cx - bw / 2, ys[0])
    ax.text(left_x - 0.15, ys[0] + 0.30, a.in_label, fontsize=11, ha="left")
    arrow(cx + bw / 2, ys[-1], right_x - 0.5, ys[-1])
    ax.text(right_x - 0.45, ys[-1] + 0.30, a.out_label, fontsize=11, ha="left")

    if fb_node:
        arrow(cx, ys[-1] - bh / 2, cx, fb_y + bh / 2)
        box(cx, fb_y, bw, bh, fb_node)
        seg(cx + bw / 2, fb_y, right_x, fb_y)
        seg(right_x, fb_y, right_x, ys[0])
        arrow(right_x, ys[0], cx + bw / 2, ys[0])
        ax.text(right_x + 0.2, (fb_y + ys[0]) / 2, a.fb_label,
                fontsize=10, rotation=90, va="center", ha="left")

    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}\\{a.out}.png", dpi=170, bbox_inches="tight")
    fig.savefig(f"{OUT_DIR}\\{a.out}.svg", bbox_inches="tight")
    plt.close(fig)
    print("saved:", f"{OUT_DIR}\\{a.out}.png")


if __name__ == "__main__":
    main()
