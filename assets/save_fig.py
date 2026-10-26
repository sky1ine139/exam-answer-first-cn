# -*- coding: utf-8 -*-
"""把生成的图保存到本地固定目录,并输出可直接内联的 Markdown 链接。

为什么改成本地:公网图床(jsDelivr / raw.githubusercontent)在国内网络下经常
被墙或超时,聊天里会显示成「图片无法预览」。DeepSeek Harness 的 GUI 支持直接
渲染本机绝对路径的图片(走 `GET /api/file?path=<绝对路径>` 这条已认证路由),
所以只要把 PNG 放在本机固定目录,内联 `![](D:/.../x.png)` 就能正常显示。

目录: ~/.dsh/exam-figs/   (Windows: C:/Users/<你>/.dsh/exam-figs/)
清理: 每次运行自动删除超过 --keep-days(默认 7)天的旧图;也可手动 `--clean`。

用法:
    python save_fig.py <图片路径> [--name 英文短名] [--keep-days 7] [--max-kb 300]
    python save_fig.py --clean [--keep-days 0]     # 立刻清空

输出:
    path     : 本地绝对路径
    markdown : ![figure](D:/.../name-20260101-120000.png)
"""
import argparse
import datetime
import os
import re
import shutil
import sys

# Windows 控制台默认 GBK,中文提示会变乱码;统一切到 UTF-8(失败则忽略)
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

FIG_DIR = os.path.join(os.path.expanduser("~"), ".dsh", "exam-figs")


def shrink(path, max_kb):
    """超过 max_kb 时自动压缩:先等比缩宽,再降 JPEG 质量。"""
    if os.path.getsize(path) / 1024 <= max_kb:
        return path
    try:
        from PIL import Image
    except ImportError:
        print(f"[warn] {os.path.basename(path)} 超过 {max_kb} KB 且未装 Pillow,无法自动压缩",
              file=sys.stderr)
        return path

    im = Image.open(path).convert("RGB")
    out = os.path.splitext(path)[0] + "_small.jpg"
    for width in (900, 800, 700, 600, 520):
        im2 = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS) \
            if im.width > width else im
        for q in (88, 80, 72, 65, 55):
            im2.save(out, "JPEG", quality=q, optimize=True)
            if os.path.getsize(out) / 1024 <= max_kb:
                print(f"[info] 已压缩到 {os.path.getsize(out) / 1024:.0f} KB "
                      f"({width}px, q={q})", file=sys.stderr)
                return out
    return out


def prune(keep_days):
    """删除超过 keep_days 天的旧图。keep_days<=0 表示全部删除。"""
    if not os.path.isdir(FIG_DIR):
        return 0
    cutoff = datetime.datetime.now() - datetime.timedelta(days=max(keep_days, 0))
    removed = 0
    for name in os.listdir(FIG_DIR):
        p = os.path.join(FIG_DIR, name)
        if not os.path.isfile(p):
            continue
        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(p))
        if keep_days <= 0 or mtime < cutoff:
            try:
                os.remove(p)
                removed += 1
            except OSError:
                pass
    return removed


def as_markdown_path(path):
    """Windows 路径转正斜杠;含空格或非 ASCII 时整体做百分号编码。"""
    p = os.path.abspath(path).replace("\\", "/")
    if re.search(r"[^\x21-\x7e]| ", p):
        from urllib.parse import quote
        return quote(p, safe="/:")
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image", nargs="?", help="本地图片路径")
    ap.add_argument("--name", default=None, help="文件名前缀(仅 ASCII);默认取原文件名")
    ap.add_argument("--keep-days", type=float, default=7.0,
                    help="保留天数,超过自动删除;默认 7 天")
    ap.add_argument("--max-kb", type=float, default=300.0, help="单文件大小上限,默认 300 KB")
    ap.add_argument("--clean", action="store_true", help="只清理,不保存新图")
    a = ap.parse_args()

    os.makedirs(FIG_DIR, exist_ok=True)
    removed = prune(a.keep_days)
    if removed:
        print(f"[info] 已清理 {removed} 张超过 {a.keep_days:g} 天的旧图", file=sys.stderr)

    if a.clean:
        print(f"目录: {FIG_DIR}")
        return
    if not a.image:
        ap.error("缺少图片路径(或用 --clean 只清理)")

    src = os.path.abspath(a.image)
    if not os.path.isfile(src):
        sys.exit(f"找不到图片: {src}")

    src = shrink(src, a.max_kb)
    ext = os.path.splitext(src)[1].lower() or ".png"
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    base = a.name or os.path.splitext(os.path.basename(src))[0]
    base = re.sub(r"[^A-Za-z0-9._-]", "-", base)[:40].strip("-") or "fig"
    fname = f"{base}-{stamp}{ext}"

    dst = os.path.join(FIG_DIR, fname)
    shutil.copy2(src, dst)

    md = as_markdown_path(dst)
    print(f"path     : {dst}")
    print(f"markdown : ![figure]({md})")


if __name__ == "__main__":
    main()
