# -*- coding: utf-8 -*-
"""把生成的图推送(commit + push)到本 skill 仓库的 figs/ 目录,并输出可直接内联的公网链接。

为什么需要它:本地图床(http://127.0.0.1:...)只在当前机器的浏览器里有效,网页版 AI、
手机、别人的电脑都打不开,临时目录一清历史对话里的图也会变空白。推到公开仓库后用
jsDelivr CDN 链接,任何客户端都能加载。

用法:
    python publish_fig.py <图片路径> [--name my-fig] [--max-kb 300] [--no-push]

输出:
    jsDelivr : https://cdn.jsdelivr.net/gh/<owner>/<repo>@main/figs/<name>.png
    raw      : https://raw.githubusercontent.com/<owner>/<repo>/main/figs/<name>.png
    markdown : ![figure](<jsDelivr 链接>)
"""
import argparse
import datetime
import os
import re
import shutil
import subprocess
import sys

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGS_DIR = os.path.join(SKILL_DIR, "figs")
# 有些机器上 git 配了本地代理(如 127.0.0.1:7897)但代理没开,推送会失败,所以推送时绕过它
PROXY_OVERRIDE = ["-c", "http.proxy=", "-c", "https.proxy="]


def run(args, check=True):
    p = subprocess.run(args, cwd=SKILL_DIR, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if check and p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout).strip())
    return p


def owner_repo():
    url = run(["git", "remote", "get-url", "origin"]).stdout.strip()
    m = re.search(r"github\.com[:/]([^/]+)/([^/.]+?)(?:\.git)?$", url)
    if not m:
        raise RuntimeError(f"无法从 remote 解析 owner/repo: {url}")
    return m.group(1), m.group(2)


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image", help="本地图片路径")
    ap.add_argument("--name", default=None, help="文件名前缀(仅 ASCII);默认取原文件名")
    ap.add_argument("--max-kb", type=float, default=300.0, help="单文件大小上限,默认 300 KB")
    ap.add_argument("--no-push", action="store_true", help="只提交不推送(离线调试用)")
    a = ap.parse_args()

    src = os.path.abspath(a.image)
    if not os.path.isfile(src):
        sys.exit(f"找不到图片: {src}")

    src = shrink(src, a.max_kb)
    ext = os.path.splitext(src)[1].lower() or ".png"
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    base = a.name or os.path.splitext(os.path.basename(src))[0]
    base = re.sub(r"[^A-Za-z0-9._-]", "-", base)[:40].strip("-") or "fig"
    fname = f"{base}-{stamp}{ext}"

    os.makedirs(FIGS_DIR, exist_ok=True)
    shutil.copy2(src, os.path.join(FIGS_DIR, fname))

    run(["git", "add", os.path.join("figs", fname)])
    run(["git", "commit", "-q", "-m", f"fig: {fname}"])
    if not a.no_push:
        run(["git"] + PROXY_OVERRIDE + ["push", "-q", "origin", "main"])

    owner, repo = owner_repo()
    cdn = f"https://cdn.jsdelivr.net/gh/{owner}/{repo}@main/figs/{fname}"
    raw = f"https://raw.githubusercontent.com/{owner}/{repo}/main/figs/{fname}"
    print(f"jsDelivr : {cdn}")
    print(f"raw      : {raw}")
    print(f"markdown : ![figure]({cdn})")


if __name__ == "__main__":
    main()
