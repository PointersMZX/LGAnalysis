# -*- coding: utf-8 -*-
"""落盘可见标识改名：yunx.* → lganalysis.*（数据目录/库/日志/备份/part 文件/深度链接等）。
只动代码与清单文件；内部文档（UPSTREAM-DIFF/Agent.md/01 报告）保留上游字样。
白名单排除项（不在 token 列表内，天然不动）：
  CYQawa/yunx_gopeed_build（内核下发仓）、yunx.cyqawa.os.kg（上游公告后端）、
  BaiduApi "yunx|" 设备哈希、__yunx* JS 注入标记、yunx:v1: 兼容前缀、
  通知频道/线程/wakelock 内部 ID（yunx_download/yunx:download/yunx-chunk-io/yunxTaskId）。
"""
import pathlib, sys

ROOT = pathlib.Path(r"D:\Agent\LGAnalysis")
EXTS = {".kt", ".kts", ".xml", ".cs", ".ps1", ".js"}
SKIP = {".git", "build", ".gradle", "release"}

TOKENS = [
    ("yunx.db", "lganalysis.db"),
    ("yunx_auth_backup", "lganalysis_auth_backup"),
    (".yunx-", ".lganalysis-"),
    ("yunx_download_debug", "lganalysis_download_debug"),
    ("yunx-preview", "lganalysis-preview"),
    ("yunx_write_probe", "lganalysis_write_probe"),
    ("yunx-bridge", "lganalysis-bridge"),
    ("yunx_settings", "lganalysis_settings"),
    ("yunx-desktop", "lganalysis-desktop"),
    ("yunx-dl", "lganalysis-dl"),
    ("yunx://", "lganalysis://"),
    (
        'node("yunx/',
        'node("lganalysis/',
    ),  # java.util.prefs 节点（yunx/misc、yunx/settings、yunx/xunlei_fp、yunx/announcement）
]


def walk():
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        if SKIP & set(p.parts):
            continue
        if p.suffix.lower() not in EXTS:
            continue
        # 只处理 desktop/ 与 android/ 代码树 + 扩展 js
        rel = p.relative_to(ROOT)
        if rel.parts[0] not in ("desktop", "android"):
            continue
        yield p


def main():
    counts = {t: 0 for t, _ in TOKENS}
    changed = 0
    for p in walk():
        s = p.read_text(encoding="utf-8", errors="replace")
        orig = s
        for pat, rep in TOKENS:
            n = s.count(pat)
            if n:
                counts[pat] += n
                s = s.replace(pat, rep)
        if s != orig:
            p.write_text(s, encoding="utf-8", newline="")
            changed += 1
            print("changed:", p.relative_to(ROOT))
    print("---")
    for pat, rep in TOKENS:
        print(f"{rep}: {counts[pat]}")
    print("files changed:", changed)


if __name__ == "__main__":
    main()
