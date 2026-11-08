# -*- coding: utf-8 -*-
"""移除双端「公告」整套功能（v2）：数据层三件 + UI 三件 + VM + MainScreen 全部接线。
共享组件（RemoteImage/RemoteImageLoader/GFM 渲染器/ImageViewerOverlay）有其他使用方，保留。
每处删除带精确断言。"""
import pathlib, sys, subprocess

ROOT = pathlib.Path(r"D:\Agent\LGAnalysis")
A_MS = ROOT / "android/app/src/main/kotlin/com/lg/analysis/ui/MainScreen.kt"
D_MS = ROOT / "desktop/desktop/src/main/kotlin/com/lg/analysis/ui/MainScreen.kt"


def cut(s, block, what, count=1):
    n = s.count(block)
    if n != count:
        print(f"ABORT {what}: found {n}, expected {count}")
        sys.exit(2)
    return s.replace(block, "")


def cut_span(s, start_marker, end_marker, what):
    i = s.find(start_marker)
    if i < 0:
        print(f"ABORT {what}: start not found"); sys.exit(2)
    j = s.find(end_marker, i)
    if j < 0:
        print(f"ABORT {what}: end not found"); sys.exit(2)
    return s[:i] + s[j + len(end_marker):]


# ============ Android MainScreen ============
s = A_MS.read_text(encoding="utf-8")
for imp in [
    "import com.lg.analysis.data.announcement.AnnouncementReadStore\n",
    "import com.lg.analysis.ui.screens.AnnouncementPopupDialog\n",
    "import com.lg.analysis.ui.screens.AnnouncementScreen\n",
    "import com.lg.analysis.ui.screens.AnnouncementUnreadBadge\n",
    "import com.lg.analysis.ui.viewmodel.AnnouncementViewModel\n",
]:
    s = cut(s, imp, "android import " + imp.strip())
s = cut(s, '/** 公告页：源是顶栏那个公告图标（与收藏页同一手法 —— 图标本身当"源"，长成整页） */\ninternal const val OVERLAY_KEY_ANNOUNCEMENTS = "overlay-announcements"\n\n', "android overlay key+doc")
s = cut(s, "    var showAnnouncements by rememberSaveable { mutableStateOf(false) }\n", "android showAnnouncements")
s = cut(s, '    /** 启动公告弹窗点「查看详情」时带进去的公告 id（null = 从图标进来先看列表） */\n    var announcementDetailId by rememberSaveable { mutableStateOf<String?>(null) }\n', "android detailId")
s = cut_span(s, "    /**\n     * 应用内公告：顶栏红点角标 + 启动弹窗。",
             "LaunchedEffect(Unit) { announcementViewModel.checkStartup() }\n\n\n", "android VM block")
s = cut(s, "        showAnnouncements -> OVERLAY_KEY_ANNOUNCEMENTS\n", "android route branch")
blk = """                            // 公告入口：所有 Tab 都显示（收藏只在解析页出现，公告是全局入口），
                            // 位置在收藏图标左侧 —— 与收藏图标共用"图标当源、长成整页"的容器变换手法。
                            //
                            // ★ 角标必须画在 IconButton **外面**（外层再套一个 48dp 的 Box）：
                            //   material3 的 IconButton 内部带 `.clip(CircleShape)`（那颗 40dp 的圆形
                            //   水波纹 StateLayer），角标一旦超出这颗圆就被切掉 —— 实测症状是红点被切成
                            //   水滴形（见用户截图）。外层 Box 与 IconButton 同为 48dp 且不裁剪；
                            //   Box 仍是同一个 48dp 点击区，而角标自身没有 pointerInput，
                            //   点在角标上的事件照旧落到 IconButton，不影响点击。
                            Box(
                                modifier = Modifier.size(48.dp),
                                contentAlignment = Alignment.Center
                            ) {
                                IconButton(
                                    onClick = {
                                        // 从图标进 = 先看列表（清掉上次「查看详情」直接进详情的请求）
                                        announcementDetailId = null
                                        showAnnouncements = true
                                    }
                                ) {
                                    Icon(
                                        imageVector = Icons.Outlined.Campaign,
                                        contentDescription = if (unreadAnnouncementCount > 0) {
                                            "公告（$unreadAnnouncementCount 条未读）"
                                        } else {
                                            "公告"
                                        },
                                        modifier = Modifier.sharedBounds(
                                            rememberSharedContentState(OVERLAY_KEY_ANNOUNCEMENTS),
                                            animatedVisibilityScope = sourceScope
                                        )
                                    )
                                }
                                // 未读红点角标：只有主界面显示（公告页自己开着的时候不显示）
                                if (unreadAnnouncementCount > 0 && overlayRoute == null) {
                                    AnnouncementUnreadBadge(
                                        count = unreadAnnouncementCount,
                                        modifier = Modifier
                                            .align(Alignment.TopEnd)
                                            .offset(x = (-6).dp, y = 2.dp)
                                    )
                                }
                            }
"""
s = cut(s, blk, "android topbar button")
blk = """                            OVERLAY_KEY_ANNOUNCEMENTS -> AnnouncementScreen(
                                viewModel = announcementViewModel,
                                onBack = { showAnnouncements = false },
                                // 启动弹窗点了「查看详情」就直接落在详情页（列表 ↔ 详情的共享元素在页面内部）
                                initialDetailId = announcementDetailId
                            )
"""
s = cut(s, blk, "android overlay when")
blk = """    // 启动公告弹窗：展示未读的置顶公告（没有则最新未读）。两个出口都算已读，见 AnnouncementViewModel.consumePopup
    popupAnnouncement?.let { announcement ->
        AnnouncementPopupDialog(
            announcement = announcement,
            onDetail = {
                announcementDetailId = announcement.id
                showAnnouncements = true
                announcementViewModel.consumePopup()
            },
            onDismiss = { announcementViewModel.consumePopup() }
        )
    }

"""
s = cut(s, blk, "android popup dialog")
residual = [l for l in s.lower().splitlines() if "announcement" in l or "公告" in l]
if residual:
    print("ABORT android residual:", residual[:5]); sys.exit(2)
A_MS.write_text(s, encoding="utf-8", newline="")
print("android MainScreen ok")

# ============ Desktop MainScreen ============
s = D_MS.read_text(encoding="utf-8")
for imp in [
    "import com.lg.analysis.data.announcement.AnnouncementReadStore\n",
    "import com.lg.analysis.ui.screens.AnnouncementPopupDialog\n",
    "import com.lg.analysis.ui.screens.AnnouncementScreen\n",
    "import com.lg.analysis.ui.screens.AnnouncementUnreadBadge\n",
    "import com.lg.analysis.ui.viewmodel.AnnouncementViewModel\n",
]:
    s = cut(s, imp, "desktop import " + imp.strip())
s = cut(s, "    var showAnnouncements by rememberSaveable { mutableStateOf(false) }\n", "desktop showAnnouncements")
s = cut(s, "    /** 启动公告弹窗点「查看详情」时带进去的公告 id（null = 从图标进来先看列表） */\n    var announcementDetailId by rememberSaveable { mutableStateOf<String?>(null) }\n", "desktop detailId")
s = cut_span(s, "    /**\n     * 应用内公告：顶栏红点角标 + 启动弹窗。",
             "LaunchedEffect(Unit) { announcementViewModel.checkStartup() }\n\n", "desktop VM block")
blk = """                    // 公告入口：所有 Tab 都显示（收藏只在解析页出现，公告是全局入口）。
                    // 角标画在 IconButton 外面（外层再套一个 48dp 的 Box）：material3 的 IconButton
                    // 内部带 .clip(CircleShape)，角标超出那颗圆会被切掉；外层 Box 同为 48dp 且不裁剪，
                    // 点击事件照旧落到 IconButton。
                    Box(
                        modifier = Modifier.size(48.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        IconButton(
                            onClick = {
                                // 从图标进 = 先看列表（清掉上次「查看详情」直接进详情的请求）
                                announcementDetailId = null
                                showAnnouncements = true
                            }
                        ) {
                            Icon(
                                imageVector = Icons.Outlined.Campaign,
                                contentDescription = if (unreadAnnouncementCount > 0) {
                                    "公告（$unreadAnnouncementCount 条未读）"
                                } else {
                                    "公告"
                                }
                            )
                        }
                        // 未读红点角标：只有主界面显示（公告页自己开着的时候不显示）
                        if (unreadAnnouncementCount > 0 && !showAnnouncements) {
                            AnnouncementUnreadBadge(
                                count = unreadAnnouncementCount,
                                modifier = Modifier
                                    .align(Alignment.TopEnd)
                                    .offset(x = (-6).dp, y = 2.dp)
                            )
                        }
                    }
"""
s = cut(s, blk, "desktop topbar button")
blk = """        // 应用内公告：叠加覆盖层（列表 ↔ 详情在页面内部切换）
        AnimatedVisibility(
            visible = showAnnouncements,
            enter = fadeIn(tween(220)) + scaleIn(tween(220), initialScale = 0.96f),
            exit = fadeOut(tween(160)) + scaleOut(tween(160), targetScale = 0.96f),
            modifier = Modifier.fillMaxSize()
        ) {
            AnnouncementScreen(
                viewModel = announcementViewModel,
                onBack = { showAnnouncements = false },
                // 启动弹窗点了「查看详情」就直接落在详情页
                initialDetailId = announcementDetailId
            )
        }

"""
s = cut(s, blk, "desktop overlay AnimatedVisibility")
blk = """        // 启动公告弹窗：展示未读的置顶公告（没有则最新未读）。两个出口都算已读，见 AnnouncementViewModel.consumePopup
        popupAnnouncement?.let { announcement ->
            AnnouncementPopupDialog(
                announcement = announcement,
                onDetail = {
                    announcementDetailId = announcement.id
                    showAnnouncements = true
                    announcementViewModel.consumePopup()
                },
                onDismiss = { announcementViewModel.consumePopup() }
            )
        }

        // 启动更新弹窗：与公告弹窗互斥（公告优先），避免两个覆盖层叠在一起看不清
        if (popupAnnouncement == null) {
"""
s = cut(s, blk, "desktop popup dialog + mutex head")
# 删除后，启动更新弹窗整块多了一层缩进（原来在 if 里）。定位该块并回退缩进。
i = s.find("            startupUpdateRelease?.let { release ->")
if i < 0:
    print("ABORT: startup update block not found"); sys.exit(2)
# 找块结束：UpdateDialog( ... ) 的收尾。找「        }\n」在块 start 之后第一处顶格为 8 空格的 "}"，它就是 if 的收尾
j = s.find("\n        }\n", i)
if j < 0:
    print("ABORT: if close not found"); sys.exit(2)
inner = s[i:j + 1]  # 含 startupUpdateRelease 行到 "        }" 前
# 回退缩进：把 inner 每行去掉 4 个前导空格（空行除外）
lines = []
for ln in inner.split("\n"):
    lines.append(ln[4:] if ln.startswith("    ") else ln)
dedented = "\n".join(lines)
# 替换：inner（在 if 内，20 空格缩进）→ dedented（16 空格，直接在 let 里）
s = s[:i] + dedented + s[j + 1:]
residual = [l for l in s.lower().splitlines() if "announcement" in l or "公告" in l]
if residual:
    print("ABORT desktop residual:", residual[:5]); sys.exit(2)
D_MS.write_text(s, encoding="utf-8", newline="")
print("desktop MainScreen ok (update dialog de-mutexed)")

# ============ 删除公告专属文件 ============
files = [
    "android/app/src/main/kotlin/com/lg/analysis/data/announcement/AnnouncementApi.kt",
    "android/app/src/main/kotlin/com/lg/analysis/data/announcement/AnnouncementReadStore.kt",
    "android/app/src/main/kotlin/com/lg/analysis/data/announcement/AnnouncementTime.kt",
    "android/app/src/main/kotlin/com/lg/analysis/ui/screens/AnnouncementDetailScreen.kt",
    "android/app/src/main/kotlin/com/lg/analysis/ui/screens/AnnouncementListScreen.kt",
    "android/app/src/main/kotlin/com/lg/analysis/ui/screens/AnnouncementScreen.kt",
    "android/app/src/main/kotlin/com/lg/analysis/ui/viewmodel/AnnouncementViewModel.kt",
    "desktop/desktop/src/main/kotlin/com/lg/analysis/data/announcement/AnnouncementApi.kt",
    "desktop/desktop/src/main/kotlin/com/lg/analysis/data/announcement/AnnouncementReadStore.kt",
    "desktop/desktop/src/main/kotlin/com/lg/analysis/data/announcement/AnnouncementTime.kt",
    "desktop/desktop/src/main/kotlin/com/lg/analysis/ui/screens/AnnouncementDetailScreen.kt",
    "desktop/desktop/src/main/kotlin/com/lg/analysis/ui/screens/AnnouncementListScreen.kt",
    "desktop/desktop/src/main/kotlin/com/lg/analysis/ui/screens/AnnouncementScreen.kt",
    "desktop/desktop/src/main/kotlin/com/lg/analysis/ui/viewmodel/AnnouncementViewModel.kt",
]
for f in files:
    r = subprocess.run(["git", "rm", "-q", str(ROOT / f)], cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        print("git rm fail:", f, r.stderr); sys.exit(2)
print("git rm", len(files), "files ok")
