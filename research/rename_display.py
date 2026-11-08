# -*- coding: utf-8 -*-
"""展示名口径：名称旁的英文名显示为 "LG Analysis"（带空格）；
仓库 URL/包名/文件名/UA/线程名/日志 TAG 等技术标识保持 "LGAnalysis"。
每处替换带出现次数断言。"""
import pathlib, sys

ROOT = pathlib.Path(r"D:\Agent\LGAnalysis")

# (相对路径, [(旧, 新, 期望次数), ...])
JOBS = [
    # ---- 桌面 ----
    ("desktop/desktop/src/main/kotlin/com/lg/analysis/Main.kt", [
        ('title = "甘露解析 LGAnalysis"', 'title = "甘露解析 LG Analysis"', 1),
    ]),
    ("desktop/desktop/src/main/kotlin/com/lg/analysis/util/SingleInstance.kt", [
        ('private const val WINDOW_TITLE = "甘露解析 LGAnalysis"', 'private const val WINDOW_TITLE = "甘露解析 LG Analysis"', 1),
    ]),
    ("desktop/desktop/src/main/kotlin/com/lg/analysis/util/TrayManager.kt", [
        ('"甘露解析 LGAnalysis"', '"甘露解析 LG Analysis"', 1),
    ]),
    ("desktop/desktop/src/main/kotlin/com/lg/analysis/ui/screens/AboutScreen.kt", [
        ('text = "LGAnalysis · v$versionName"', 'text = "LG Analysis · v$versionName"', 1),
        ('description = "甘露解析（LGAnalysis）是一款网盘分享链接 + 视频链接解析与高速下载工具。', 'description = "甘露解析（LG Analysis）是一款网盘分享链接 + 视频链接解析与高速下载工具。', 1),
        ('description = "甘露解析（LGAnalysis）是一款网盘 / 视频分享链接解析与高速下载工具。', 'description = "甘露解析（LG Analysis）是一款网盘 / 视频分享链接解析与高速下载工具。', 1),
    ]),
    ("desktop/desktop/src/main/kotlin/com/lg/analysis/ui/screens/OnboardingScreen.kt", [
        ('text = "LGAnalysis · v$APP_VERSION"', 'text = "LG Analysis · v$APP_VERSION"', 1),
    ]),
    ("desktop/desktop/src/main/kotlin/com/lg/analysis/util/LogExporter.kt", [
        ('appendLine("甘露解析 LGAnalysis 运行日志")', 'appendLine("甘露解析 LG Analysis 运行日志")', 1),
        ('"甘露解析 LGAnalysis 日志导出 ', '"甘露解析 LG Analysis 日志导出 ', 1),
    ]),
    ("desktop/desktop/src/main/kotlin/com/lg/analysis/data/download/DownloadDebugLog.kt", [
        ('appendLine("甘露解析 LGAnalysis 下载调试日志")', 'appendLine("甘露解析 LG Analysis 下载调试日志")', 1),
    ]),
    ("desktop/desktop/src/main/kotlin/com/lg/analysis/ui/screens/DownloadDebugScreen.kt", [
        ('appendLine("甘露解析 LGAnalysis 下载调试快照")', 'appendLine("甘露解析 LG Analysis 下载调试快照")', 1),
    ]),
    # ---- Android ----
    ("android/app/src/main/kotlin/com/lg/analysis/ui/screens/AboutScreen.kt", [
        ('text = "LGAnalysis · v$versionName ($versionCode)"', 'text = "LG Analysis · v$versionName ($versionCode)"', 1),
        ('description = "甘露解析（LGAnalysis）是一款网盘 / 视频分享链接解析与高速下载工具。', 'description = "甘露解析（LG Analysis）是一款网盘 / 视频分享链接解析与高速下载工具。', 1),
    ]),
    ("android/app/src/main/kotlin/com/lg/analysis/ui/screens/OnboardingScreen.kt", [
        ('text = "LGAnalysis · v$versionName"', 'text = "LG Analysis · v$versionName"', 1),
    ]),
    # ---- 安装器（AppPublisher 显示在"发布者"字段，跟展示名走）----
    ("desktop/installer/LGAnalysis.iss", [
        ('#define AppNameEn "LGAnalysis"', '#define AppNameEn "LG Analysis"', 1),
    ]),
]


def main():
    for rel, pairs in JOBS:
        p = ROOT / rel
        s = p.read_text(encoding="utf-8")
        for old, new, expect in pairs:
            n = s.count(old)
            if n != expect:
                print(f"ABORT {rel}: {old[:50]!r} found {n}, expected {expect}")
                sys.exit(2)
            s = s.replace(old, new)
        p.write_text(s, encoding="utf-8", newline="")
        print("ok:", rel)


if __name__ == "__main__":
    main()
