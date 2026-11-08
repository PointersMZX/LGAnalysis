# -*- coding: utf-8 -*-
"""落盘标识改名的手工项：精确替换 + 断言计数，缺一即退出码 2"""
import pathlib, sys

ROOT = pathlib.Path(r"D:\Agent\LGAnalysis")


def patch(rel, pairs):
    p = ROOT / rel
    s = p.read_text(encoding="utf-8")
    for old, new, expect in pairs:
        n = s.count(old)
        if n != expect:
            print(f"ABORT {rel}: {old!r} found {n}, expected {expect}")
            sys.exit(2)
        s = s.replace(old, new)
    p.write_text(s, encoding="utf-8", newline="")
    print("ok:", rel)


# 1) AppContext：删旧版（上游 .yunx-pc）数据目录迁移块——本产品无存量旧数据
p = ROOT / "desktop/desktop/src/main/kotlin/com/lg/analysis/AppContext.kt"
s = p.read_text(encoding="utf-8")
block1 = "    /** 旧版数据根目录（.lganalysis-pc）：首次启动时整体迁移到新目录 */\n    private val legacyDataDir: File = File(System.getProperty(\"user.home\"), \".lganalysis-pc\")\n\n"
assert s.count(block1) == 1, "legacyDataDir property not found"
s = s.replace(block1, "")
assert s.count("        migrateLegacyDataDir()\n") == 1, "migrate call not found"
s = s.replace("        migrateLegacyDataDir()\n", "")
i = s.index("    /**\n     * 旧数据目录迁移：<用户目录>/.lganalysis-pc")
j = s.index("\n", s.index("已迁移数据目录", i))
end = s.index("    }\n", j) + len("    }\n") + 1
s = s[:i] + s[end:]
p.write_text(s, encoding="utf-8", newline="")
print("ok: AppContext legacy block removed")

# 2) AndroidManifest：alias 名 + scheme
patch("android/app/src/main/AndroidManifest.xml", [
    ("com.lg.analysis.link.YunxLink", "com.lg.analysis.link.LGAnalysisLink", 1),
    ('<data android:scheme="yunx" />', '<data android:scheme="lganalysis" />', 1),
])

# 3) LinkOpenTarget 枚举里的组件名
patch("android/app/src/main/kotlin/com/lg/analysis/data/prefs/LinkOpenTarget.kt", [
    ("com.lg.analysis.link.YunxLink", "com.lg.analysis.link.LGAnalysisLink", 1),
])

# 4) Launcher.cs 注册表路径
patch("desktop/launcher/Launcher.cs", [
    (r"yunx\settings", r"lganalysis\settings", 2),
])

# 5) 扩展端 app 字段校验（与桌面 BrowserBridgeServer 同步）
patch("desktop/browser-extension/background.js", [
    ("j.app === 'yunx'", "j.app === 'lganalysis'", 1),
])
patch("desktop/desktop/src/main/kotlin/com/lg/analysis/data/bridge/BrowserBridgeServer.kt", [
    ('.put("app", "yunx")', '.put("app", "lganalysis")', 1),
])

# 6) 备份文件扩展名 .yunx → .enc（桌面 + 移动各一份）
for rel in ("desktop/desktop/src/main/kotlin/com/lg/analysis/data/backup/AuthBackupManager.kt",
            "android/app/src/main/kotlin/com/lg/analysis/data/backup/AuthBackupManager.kt"):
    p = ROOT / rel
    s = p.read_text(encoding="utf-8")
    n = s.count('"${if (encrypted) "yunx" else "json"}"') + s.count('${if (encrypted) "yunx" else "json"}')
    s2 = s.replace('${if (encrypted) "yunx" else "json"}', '${if (encrypted) "enc" else "json"}')
    s2 = s2.replace(".yunx（加密备份）", ".enc（加密备份）")
    if s2 == s:
        print(f"ABORT {rel}: no .yunx extension token found")
        sys.exit(2)
    p.write_text(s2, encoding="utf-8", newline="")
    print("ok:", rel)

# 7) 生成代码目录名
patch("desktop/desktop/build.gradle.kts", [
    ('resolve("com/yunx/app")', 'resolve("com/lg/analysis")', 1),
])
print("ALL MANUAL PATCHES OK")
