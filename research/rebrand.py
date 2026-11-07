# -*- coding: utf-8 -*-
"""甘露解析 LGAnalysis 改造脚本：品牌/群号/仓库/版本/关于页/删除支持开发（双端一次到位）"""
import pathlib
import re
import sys

ROOT = pathlib.Path(r"D:\Agent\LGAnalysis")
ERR = []

def load(rel):
    return (ROOT / rel).read_text(encoding="utf-8")

def save(rel, s):
    (ROOT / rel).write_text(s, encoding="utf-8", newline="")

def edit(rel, old, new, expect=1):
    EDITS.append((rel, old, new, expect))

def cut(rel, start_marker, end_marker):
    """删除 [start_marker, end_marker) 区间（含 start，不含 end）"""
    CUTS.append((rel, start_marker, end_marker))

def validate_and_apply():
    fails = 0
    for rel, old, new, expect in EDITS:
        n = load(rel).count(old)
        if n != expect:
            print(f"[校验失败] [{rel}] 期望 {expect} 处，实际 {n} 处：{old[:80]!r}")
            fails += 1
    for rel, start, end in CUTS:
        s = load(rel)
        i, j = s.find(start), s.find(end)
        if i < 0 or j < 0 or j <= i:
            print(f"[校验失败] [{rel}] cut 区间定位失败：{start[:60]!r}")
            fails += 1
    if fails:
        print(f"共 {fails} 个模式未命中，已中止（未写入任何文件）")
        sys.exit(2)
    for rel, old, new, expect in EDITS:
        save(rel, load(rel).replace(old, new))
    for rel, start, end in CUTS:
        s = load(rel)
        i, j = s.find(start), s.find(end)
        save(rel, s[:i] + s[j:])
    print(f"结构编辑 OK：{len(EDITS)} 个替换 + {len(CUTS)} 个区间删除")

EDITS = []
CUTS = []

# ============ Phase 1：显式结构编辑（先声明，validate_and_apply 统一落盘） ============

# ---- Android AppLinks：新群号常量 + 加群短链 ----
edit("android/app/src/main/kotlin/com/yunx/app/util/AppLinks.kt",
     '''    /** QQ 交流群群号（引导页首页、设置页「关于」组都有入口） */
    const val QQ_GROUP = "635207650"
''',
     '''    /** QQ 交流群群号（引导页首页、设置页「关于」组都有入口） */
    const val QQ_GROUP = "335753296"

    /** QQ 官方加群短链（浏览器/QQ 打开即出现加群卡片；群号换绑时这里和 [QQ_GROUP] 要一起改） */
    const val QQ_GROUP_JOIN_URL = "https://qm.qq.com/q/soFNtWRytq"
''')
edit("android/app/src/main/kotlin/com/yunx/app/util/AppLinks.kt",
     '''    fun openQQGroup(context: Context): Boolean {
        val intent = Intent(Intent.ACTION_VIEW, Uri.parse(qqGroupScheme()))
        return runCatching { context.startActivity(intent) }.isSuccess
    }
''',
     '''    fun openQQGroup(context: Context): Boolean {
        // 先试官方加群短链（浏览器打开出现加群卡片），再退 mqqapi 群卡片 scheme；
        // 都不行时由调用方退复制群号，保证入口永远可用
        runCatching {
            context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(QQ_GROUP_JOIN_URL)))
        }.onSuccess { return true }
        val intent = Intent(Intent.ACTION_VIEW, Uri.parse(qqGroupScheme()))
        return runCatching { context.startActivity(intent) }.isSuccess
    }
''')

# ---- Android 版本 ----
edit("android/app/build.gradle.kts", "versionCode = 15", "versionCode = 1")
edit("android/app/build.gradle.kts", 'versionName = "1.3.1"', 'versionName = "1.0.0"')

# ---- 桌面版本 ----
edit("desktop/version.txt", "1.3.3\nBeta=0", "1.0.0\nBeta=0")

# ---- 桌面主窗口标题（先于全局清扫，避免残留 YunX-Desktop）----
edit("desktop/desktop/src/main/kotlin/com/yunx/app/Main.kt",
     'title = "云析 YunX-Desktop",', 'title = "甘露解析 LGAnalysis",')

# ---- Android 关于页：描述/版权行 ----
edit("android/app/src/main/kotlin/com/yunx/app/ui/screens/AboutScreen.kt",
     '''                description = "云析（YunX）是一款网盘 / 视频分享链接解析与高速下载工具。" +''',
     '''                description = "甘露解析（LGAnalysis）是一款网盘 / 视频分享链接解析与高速下载工具。" +''')
edit("android/app/src/main/kotlin/com/yunx/app/ui/screens/AboutScreen.kt",
     '''                text = "云析 v$versionName · Made with ❤ and deepseek",''',
     '''                text = "Copyright © 2026 LGAnalysis All Rights Reserved",''')

# ---- 桌面关于页：描述/版权行 ----
edit("desktop/desktop/src/main/kotlin/com/yunx/app/ui/screens/AboutScreen.kt",
     '''                description = "云析（YunX）是一款网盘分享链接 + 视频链接解析与高速下载工具。" +
                    "粘贴分享链接或视频短链，登录账号后即可浏览内容、在线预览并直接高速下载；" +
                    "也支持磁力 / BT 种子 / ed2k 等 P2P 链接下载。\\n" +
                    "Windows 桌面端：YunX-Desktop 基于 Compose Multiplatform 构建，" +
                    "在安卓版能力之上补齐桌面交互（右键菜单、文件夹整夹下载、可拖动窗口）。"''',
     '''                description = "甘露解析（LGAnalysis）是一款网盘分享链接 + 视频链接解析与高速下载工具。" +
                    "粘贴分享链接或视频短链，登录账号后即可浏览内容、在线预览并直接高速下载；" +
                    "也支持磁力 / BT 种子 / ed2k 等 P2P 链接下载。\\n" +
                    "Windows 桌面端与 Android 端同属本项目：桌面端基于 Compose Multiplatform 构建，" +
                    "在安卓版能力之上补齐桌面交互（右键菜单、文件夹整夹下载、可拖动窗口）。"''')
edit("desktop/desktop/src/main/kotlin/com/yunx/app/ui/screens/AboutScreen.kt",
     '''                text = "云析 v$versionName · Made with ❤ and deepseek",''',
     '''                text = "Copyright © 2026 LGAnalysis All Rights Reserved",''')

# ---- 桌面关于页：删除 PC 版仓库卡片（统一单仓库）+ 删函数体 ----
edit("desktop/desktop/src/main/kotlin/com/yunx/app/ui/screens/AboutScreen.kt",
     '''            GitHubCard()
            Spacer(modifier = Modifier.height(8.dp))
            DesktopRepoCard()

            Spacer(modifier = Modifier.height(8.dp))
            QQGroupCard()''',
     '''            GitHubCard()

            Spacer(modifier = Modifier.height(8.dp))
            QQGroupCard()''')
cut("desktop/desktop/src/main/kotlin/com/yunx/app/ui/screens/AboutScreen.kt",
    "/** PC 版仓库入口卡片 */", "/** QQ 交流群入口：点击复制群号")

# ---- 桌面 QQ 入口改为「打开加群短链，失败退复制」 ----
for rel in ("desktop/desktop/src/main/kotlin/com/yunx/app/ui/screens/AboutScreen.kt",
            "desktop/desktop/src/main/kotlin/com/yunx/app/ui/screens/OnboardingScreen.kt"):
    edit(rel,
         'private const val QQ_GROUP = "635207650"',
         'private const val QQ_GROUP = "335753296"\n\n'
         '/** QQ 官方加群短链（浏览器打开出现加群卡片；群号换绑时这里和 QQ_GROUP 要一起改） */\n'
         'private const val QQ_GROUP_JOIN_URL = "https://qm.qq.com/q/soFNtWRytq"')
edit("desktop/desktop/src/main/kotlin/com/yunx/app/ui/screens/AboutScreen.kt",
     '''        onClick = {
            DesktopActions.copyToClipboard(QQ_GROUP)
            SnackbarController.show("QQ 群号已复制：$QQ_GROUP")
        },''',
     '''        onClick = {
            // 先开官方加群短链（浏览器打开出现加群卡片），失败退回复制群号
            if (!DesktopActions.openUrl(QQ_GROUP_JOIN_URL)) {
                DesktopActions.copyToClipboard(QQ_GROUP)
                SnackbarController.show("QQ 群号已复制：$QQ_GROUP")
            }
        },
        modifier = Modifier.fillMaxWidth(),
        shape = MaterialTheme.shapes.large,
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.primaryContainer
        )''')
edit("desktop/desktop/src/main/kotlin/com/yunx/app/ui/screens/AboutScreen.kt",
     '''                    text = "群号：$QQ_GROUP（点击复制）",''',
     '''                    text = "群号：$QQ_GROUP（点击加入群聊）",''')
edit("desktop/desktop/src/main/kotlin/com/yunx/app/ui/screens/OnboardingScreen.kt",
     '''        onClick = {
            DesktopActions.copyToClipboard(QQ_GROUP)
            SnackbarController.show("QQ 群号已复制：$QQ_GROUP")
        },
        shape = CircleShape,''',
     '''        onClick = {
            // 先开官方加群短链（浏览器打开出现加群卡片），失败退回复制群号
            if (!DesktopActions.openUrl(QQ_GROUP_JOIN_URL)) {
                DesktopActions.copyToClipboard(QQ_GROUP)
                SnackbarController.show("QQ 群号已复制：$QQ_GROUP")
            }
        },
        shape = CircleShape,''')

# ---- Android 首启/关于副标题品牌行 ----
edit("android/app/src/main/kotlin/com/yunx/app/ui/screens/OnboardingScreen.kt",
     '            text = "YunX · v$versionName",',
     '            text = "LGAnalysis · v$versionName",')
edit("android/app/src/main/kotlin/com/yunx/app/ui/screens/AboutScreen.kt",
     '            text = "YunX · v$versionName ($versionCode)",',
     '            text = "LGAnalysis · v$versionName ($versionCode)",')
edit("desktop/desktop/src/main/kotlin/com/yunx/app/ui/screens/AboutScreen.kt",
     '                text = "YunX-Desktop · v$versionName",',
     '                text = "LGAnalysis · v$versionName",')

# ---- Android 设置页：删「支持开发」行 + 参数 + 注释 ----
edit("android/app/src/main/kotlin/com/yunx/app/ui/screens/SettingsScreen.kt",
     '''        Spacer(modifier = Modifier.height(ListGroupGap))
        SettingsItem(
            icon = Icons.Outlined.VolunteerActivism,
            shape = listGroupShape(ListGroupPos.MIDDLE),
            title = "支持开发",
            description = "微信扫码捐赠，支持项目持续维护",
            modifier = supportRowModifier,
            onClick = onSupportClick
        )

''', "")
edit("android/app/src/main/kotlin/com/yunx/app/ui/screens/SettingsScreen.kt",
     "    supportRowModifier: Modifier = Modifier,\n", "")
edit("android/app/src/main/kotlin/com/yunx/app/ui/screens/SettingsScreen.kt",
     "    onSupportClick: () -> Unit,\n", "")
edit("android/app/src/main/kotlin/com/yunx/app/ui/screens/SettingsScreen.kt",
     "分别挂到「主题与外观 / 关于云析 / 支持开发 / 下载引擎」这四行上。",
     "分别挂到「主题与外观 / 关于云析 / 下载引擎」这三行上。")

# ---- Android MainScreen：拆支持开发接线 ----
A_MAIN = "android/app/src/main/kotlin/com/yunx/app/ui/MainScreen.kt"
edit(A_MAIN, "        showSupport -> OVERLAY_KEY_SUPPORT\n", "")
edit(A_MAIN,
     '''                val supportRowModifier = Modifier.sharedBounds(
                    rememberSharedContentState(OVERLAY_KEY_SUPPORT),
                    animatedVisibilityScope = sourceScope
                )
''', "")
edit(A_MAIN, "                                    supportRowModifier = supportRowModifier,\n", "")
edit(A_MAIN, "                                    onSupportClick = { showSupport = true },\n", "")
edit(A_MAIN, "                            OVERLAY_KEY_SUPPORT -> SupportScreen(onBack = { showSupport = false })\n", "")
edit(A_MAIN, "    var showSupport by rememberSaveable { mutableStateOf(false) }\n", "")
edit(A_MAIN, 'internal const val OVERLAY_KEY_SUPPORT = "overlay-support"\n', "")
edit(A_MAIN, "import com.yunx.app.ui.screens.SupportScreen\n", "")

# ---- 桌面设置页：删行 + 参数 ----
D_SET = "desktop/desktop/src/main/kotlin/com/yunx/app/ui/screens/SettingsScreen.kt"
edit(D_SET,
     '''        Spacer(modifier = Modifier.height(8.dp))
        SettingsItem(
            icon = Icons.Outlined.VolunteerActivism,
            title = "支持开发",
            description = "微信扫码捐赠，支持项目持续维护",
            onClick = onSupportClick
        )
''', "")
edit(D_SET, "    onSupportClick: () -> Unit,\n", "")

# ---- 桌面 MainScreen：拆接线 ----
D_MAIN = "desktop/desktop/src/main/kotlin/com/yunx/app/ui/MainScreen.kt"
edit(D_MAIN, "import com.yunx.app.ui.screens.SupportScreen\n", "")
edit(D_MAIN, "    var showSupport by rememberSaveable { mutableStateOf(false) }\n", "")
edit(D_MAIN, "                            onSupportClick = { showSupport = true },\n", "")
edit(D_MAIN,
     '''        // 支持开发：叠加覆盖层
        AnimatedVisibility(
            visible = showSupport,
            enter = fadeIn(tween(220)) + scaleIn(tween(220), initialScale = 0.96f),
            exit = fadeOut(tween(160)) + scaleOut(tween(160), targetScale = 0.96f),
            modifier = Modifier.fillMaxSize()
        ) {
            SupportScreen(
                onBack = { showSupport = false }
            )
        }

''', "")

# ---- 删除 SupportScreen 源文件 ----
for rel in ("android/app/src/main/kotlin/com/yunx/app/ui/screens/SupportScreen.kt",
            "desktop/desktop/src/main/kotlin/com/yunx/app/ui/screens/SupportScreen.kt"):
    p = ROOT / rel
    if p.exists():
        p.unlink()
    else:
        ERR.append(f"[{rel}] 待删文件不存在")

# ---- 安卓安装器可见名（Inno：仅改显示名，exe 文件名不动） ----
edit("desktop/installer/YunX-Desktop.iss", '#define AppName "云析"', '#define AppName "甘露解析"')
edit("desktop/installer/YunX-Desktop.iss", '#define AppNameEn "YunX-Desktop"', '#define AppNameEn "LGAnalysis"')

# ============ Phase 1 落盘：统一校验后应用 ============
validate_and_apply()

# ============ Phase 2：全局 URL / 群号替换 ============
GLOBAL = [
    ("https://github.com/CYQawa/YunX", "https://github.com/PointersMZX/LGAnalysis"),
    ("github.com/CYQawa/YunX", "github.com/PointersMZX/LGAnalysis"),
    ("https://github.com/tidain/YunX-Desktop", "https://github.com/PointersMZX/LGAnalysis"),
    ("github.com/tidain/YunX-Desktop", "github.com/PointersMZX/LGAnalysis"),
    ("CYQawa/YunX", "PointersMZX/LGAnalysis"),
    ("tidain/YunX-Desktop", "PointersMZX/LGAnalysis"),
    ("description=YunX", "description=LGAnalysis"),
    ("635207650", "335753296"),
]
targets = [p for p in ROOT.rglob("*") if p.is_file()
           and p.suffix in (".kt", ".kts", ".xml", ".json", ".md", ".txt", ".ps1", ".iss", ".yml", ".yaml", ".html", ".properties")
           and ".git" not in p.parts
           and "release" not in p.parts[:1]]
counts = {}
for pat, rep in GLOBAL:
    counts[pat] = 0
    for p in targets:
        try:
            s = p.read_text(encoding="utf-8")
        except Exception:
            continue
        if pat in s:
            counts[pat] += s.count(pat)
            p.write_text(s.replace(pat, rep), encoding="utf-8", newline="")

# ============ Phase 3：用户可见品牌串清扫 ============
# 3a Kotlin：仅字符串字面量内的 云析→甘露解析；注释不动
kt_files = [p for p in ROOT.rglob("*.kt") if ".git" not in p.parts]
lit = re.compile(r'"((?:[^"\\\n]|\\.)*)"')
sweep_n = 0
for p in kt_files:
    s = p.read_text(encoding="utf-8")
    if "云析" not in s:
        continue
    out, changed = [], False
    for line in s.splitlines(keepends=True):
        if "云析" in line:
            def sub(m):
                global sweep_n
                inner = m.group(1)
                if "云析" in inner:
                    sweep_n += 1
                    return '"' + inner.replace("云析", "甘露解析") + '"'
                return m.group(0)
            new_line = lit.sub(sub, line)
            if new_line != line:
                changed = True
            out.append(new_line)
        else:
            out.append(line)
    if changed:
        p.write_text("".join(out), encoding="utf-8", newline="")

# 3b 字符串字面量内的（YunX）→（LGAnalysis）
for p in kt_files:
    s = p.read_text(encoding="utf-8")
    if "（YunX）" in s:
        p.write_text(s.replace("（YunX）", "（LGAnalysis）"), encoding="utf-8", newline="")

# 3c Android res XML：全部替换（文本节点即界面文案）
for p in (ROOT / "android").rglob("*.xml"):
    s = p.read_text(encoding="utf-8")
    if "云析" in s:
        p.write_text(s.replace("云析", "甘露解析"), encoding="utf-8", newline="")

# 3d fastlane 商店文案
for p in (ROOT / "android").rglob("*.txt"):
    s = p.read_text(encoding="utf-8")
    if "云析" in s:
        p.write_text(s.replace("云析", "甘露解析"), encoding="utf-8", newline="")

# 3e 浏览器扩展
for p in (ROOT / "desktop/browser-extension").rglob("*"):
    if p.is_file() and p.suffix in (".json", ".html", ".js", ".md"):
        s = p.read_text(encoding="utf-8")
        if "云析" in s:
            p.write_text(s.replace("云析", "甘露解析"), encoding="utf-8", newline="")

# 剪贴板标签
for rel in ("android/app/src/main/kotlin/com/yunx/app/ui/screens/OnboardingScreen.kt",):
    edit(rel, '"yunx_qq_group"', '"lganalysis_qq_group"')

print("sweep string literals:", sweep_n)
for pat, n in counts.items():
    print("global", pat, "->", n)
if ERR:
    print("\n== ERRORS ==")
    for e in ERR:
        print(e)
    sys.exit(1)
print("ALL EDITS OK")
