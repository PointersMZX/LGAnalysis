# -*- coding: utf-8 -*-
"""甘露解析全量换装：包名 com.yunx.app→com.lg.analysis、YunX→LGAnalysis、文档清扫"""
import pathlib, subprocess, sys

ROOT = pathlib.Path(r"D:\Agent\LGAnalysis")
TEXT_EXT = {".kt", ".kts", ".xml", ".cs", ".md", ".json", ".js", ".ps1", ".iss",
            ".yml", ".yaml", ".properties", ".txt", ".bat", ".toml", ".cfg", ".html"}
SKIP_DIRS = {".git", "release", "build", ".gradle", "node_modules"}

def all_text_files():
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        if SKIP_DIRS & set(p.parts):
            continue
        if p.suffix.lower() in TEXT_EXT:
            yield p

def git_mv(src_rel, dst_rel):
    subprocess.run(["git", "mv", str(ROOT / src_rel), str(ROOT / dst_rel)],
                   check=True, cwd=ROOT, capture_output=True)

# ---- 1) Kotlin 包目录移动 ----
moves = []
for base in ("android/app/src/main", "android/app/src/androidTest", "android/app/src/test",
             "desktop/desktop/src/main", "desktop/desktop/src/test"):
    src = f"{base}/kotlin/com/yunx/app"
    if (ROOT / src).exists():
        (ROOT / f"{base}/kotlin/com/lg").mkdir(parents=True, exist_ok=True)
        git_mv(src, f"{base}/kotlin/com/lg/analysis")
        moves.append(src)
print("moved:", moves)
try:
    # 清空的 com/yunx 目录
    for base in ("android/app/src/main", "android/app/src/androidTest", "android/app/src/test",
                 "desktop/desktop/src/main", "desktop/desktop/src/test"):
        yunx_dir = ROOT / f"{base}/kotlin/com/yunx"
        if yunx_dir.exists() and not any(yunx_dir.iterdir()):
            yunx_dir.rmdir()
except Exception as e:
    print("yunx dir cleanup:", e)

# ---- 2) 内容替换（先具体后泛化） ----
REPL = [
    ("com.yunx.app", "com.lg.analysis"),
    ("com.yunx", "com.lg.analysis"),          # 兜底：覆盖 com.yunx.app 之外的裸引用
    ("云析", "甘露解析"),                        # md 文档兜底（kt 已在上轮换过）
    ("YunX-Desktop", "LGAnalysis"),
    ("YunX-PositionPicker", "LGAnalysis-PositionPicker"),
    ("YunX-nightly", "LGAnalysis-nightly"),
    ("YunXDesktop", "LGAnalysis"),
    ("YunX", "LGAnalysis"),                   # 泛化：日志 TAG / jpackage 名 / 模块名 / 文档
]
counts = {p: 0 for p, _ in REPL}
for p in all_text_files():
    s = p.read_text(encoding="utf-8", errors="replace")
    orig = s
    for pat, rep in REPL:
        if pat in s:
            counts[pat] += s.count(pat)
            s = s.replace(pat, rep)
    if s != orig:
        p.write_text(s, encoding="utf-8", newline="")
for pat, n in counts.items():
    print("replace", pat, "->", n)

# ---- 3) 文件改名 ----
renames = [
    ("desktop/YunX-Desktop.ico", "desktop/LGAnalysis.ico"),
    ("desktop/installer/YunX-Desktop.iss", "desktop/installer/LGAnalysis.iss"),
]
for src, dst in renames:
    sp, dp = ROOT / src, ROOT / dst
    if sp.exists():
        git_mv(src, dst)
        print("renamed", src)

# ---- 4) 残留核查 ----
leftover = []
for p in all_text_files():
    s = p.read_text(encoding="utf-8", errors="replace")
    for pat in ("com.yunx", "YunX", "云析"):
        if pat in s:
            leftover.append((str(p.relative_to(ROOT)), pat))
if leftover:
    print("LEFTOVER:")
    for f, pat in leftover[:40]:
        print(" ", pat, f)
else:
    print("NO LEFTOVER")
