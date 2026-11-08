# 甘露解析（LG Analysis）前期准备 —— 甘露解析 LGAnalysis 源码分析报告

> 日期：2026-11-07　|　性质：内部开发文档（可记录参考物来源）
> 参考资料：D:\Agent\example\LGAnalysis-master.zip（Android 端）、LGAnalysis-main.zip（Windows 桌面端）
> ★ 本轮参考资料为**完整开源源码**（非二进制），无需二进制逆向；REA 用于浏览器扩展 JS 应用图分析（证据 ID ev_c7f155…/ev_3442ce…）。
> 项目已由「甘露工具箱 LGTOOLS」更名为「**甘露解析（LG Analysis）**」，目录 D:\Agent\LGAnalysis。

---

## 一、参考软件身份认定

| 项 | 内容 |
|---|---|
| 名称 | 甘露解析 · LGAnalysis（Android 端 PointersMZX/LGAnalysis；官方 Windows 桌面版 PointersMZX/LGAnalysis，作者独立维护） |
| 定位 | **粘贴网盘分享链接/视频作品链接 → 直接解析出直链并高速下载**（正是上一轮 Voyage 悬案「网盘解析」的同类完整实现） |
| 协议 | **AGPL-3.0**（作者明示：完全免费开源，收费版本均为二次打包诈骗） |
| 技术栈 | Android：Kotlin + Jetpack Compose M3 + OkHttp 4.12 + Room + Media3/Coil3（285 个 .kt，约 8.9 万行）；桌面：Compose Multiplatform + JCEF(Chromium 132) + sqlite-jdbc（282 个 .kt，约 9.2 万行）+ 自带 native/darkmode.cpp；浏览器扩展：Chrome/Edge MV3 |
| 附加 | tools/patch-gopeed-classes.py（补丁 gopeed Java 桥）、installer/portable 双分发（安装版+免安装便携版） |

## 二、支持平台矩阵（全部实现都在源码里，逐文件可查）

**网盘分享解析（10 平台 + GitHub）**：夸克、UC、迅雷、百度（⚠官方自注：可能风控账号，不建议）、139（和彩云）、123 云盘、115、光鸭云盘、蓝奏云、蓝奏云优享版、GitHub（仓库/文件直链，Token 仅提额）
**视频/图集解析（7 平台）**：抖音、小红书、快手、微博、AcFun、哔哩哔哩（登录才有高清；音视频分轨由应用内部合轨）、Pixiv（粘贴浏览器 Cookie 解析全部作品）
**P2P（桌面端）**：磁力 magnet / BT 种子（本地 .torrent 导入）/ ed2k，交由 Gopeed 引擎

## 三、核心架构与实现要点（甘露解析直接可借鉴的规格）

### 3.1 链接识别与提取码（data/network/ShareLinkParser.kt，188 行）
- 每平台一条正则识别 share_id（如夸克 `pan.quark.cn/s/([A-Za-z0-9]+)`、百度 `1[A-Za-z0-9_-]+` 前缀、115 `sw` 11 位、123 含中划线 ShareKey、139 走 shareweb 路径、蓝奏云域名族 `lanzou*/lan[zs]o[ux]/lanzn` 且与优享版 ilanzou 前置边界区分防误判）
- 提取码自动匹配 = URL 参数（pwd/pass/passcode/password）+ 文案正则 `（提取码|访问码|密码)[：:]\s*([A-Za-z0-9]{4,8})`，**没有云端提取码库**
- 解析结果统一为 `ParsedShare(shareId, pwd, platform)`

### 3.2 平台适配器四件套模式（data/network + data/repository，每平台一组）
`XxxApi.kt`（协议）+ `XxxConstants.kt`（端点/常量）+ `XxxAccountRepository.kt`（登录/Cookie）+ `XxxResolveRepository.kt`（分享解析/转存/取直链）。
- **账号形态三分**：WebView Cookie（夸克/UC/百度/139/115）；账号密码换 JWT（123）或账密/短信（迅雷/光鸭/蓝奏）；迅雷另有设备指纹 XunleiDeviceFingerprint 与口令 Kouling 机制、115 有 Pan115Crypto、139 有口令与设备信息
- **临时转存清理策略**：百度/迅雷/光鸭取链后清理，夸克保留到下载完成后清理（平台风控差异的差异化处理）
- 直链请求逐次带 Referer/Cookie 防止 403

### 3.3 下载引擎（data/download + data/gopeed）
- **内置分片下载器**：Range 分片并发（上限 32）+ 弹性区按字节顺序分配 + 断点续传（.plan 文件保存 total/chunks/chunkSize 恢复校验）+ 失败重试 + 全局限速；HlsDownloader 处理 m3u8；HlsRequestPolicy 管请求头
- **P2P 引擎 = Gopeed**（Go 运行时 libgojni.so 以 AAR 分发，Java 桥 12KB，用 tools/patch-gopeed-classes.py 打补丁绕 loadLibrary 重复加载；内核云端按 ABI 下发 CYQawa/yunx_gopeed_build，夸克 CDN 按连接限速故下载内核也走分片并发）；桌面端有 Tracker 管理页 / DHT 开关 / peer 实时概览（种子 N·连接 M·节点 K）
- **B 站 DASH 合轨**：MediaExtractor+MediaMuxer 逐样本重封装不重编码；mp4parser 读不了 B 站分片（时长在 tfhd、DTS 在 tfdt），自写 moof/trun/tfhd/tfdt/trex 解析，普通 MP4 仍走 mp4parser 兜底
- 附带 AudioExtractor（音频提取）、MotionPhotoWriter（动态照片）、DownloadPathPolicy（目录策略）、下载自动归组（文件夹/批量图集折叠分组）

### 3.4 桌面端独有设计（UPSTREAM-DIFF.md 逐条核对过）
- 内嵌 Chromium 网页登录 + **一键导入本机浏览器 Cookie**（扫 Chrome/Edge/Firefox/360/QQ，Windows DPAPI 解密；Chrome/Edge 新版应用绑定加密可能读不到，Firefox/360 始终可用）
- Windows 通知中心原地刷新 toast 进度（多任务聚合一条）+ 送达自检 + AppUserModelID 快捷方式兜底
- 托盘：AWT TrayIcon + JNA 手写 Win32 原生右键菜单（CreatePopupMenu/AppendMenuW/TrackPopupMenuEx）+ native/darkmode.cpp 暗色菜单桥
- SetThreadExecutionState「下载时阻止休眠」；前台时轮询剪贴板弹出分享链接提示卡；IFileDialog 原生对话框；explorer /select 定位文件

### 3.5 周边机制
- 更新：GitHub Releases API（正式/预发布双通道）+ cdn.gh-proxy.org 镜像前缀（GFW 下载兜底）
- 公告：独立 AnnouncementApi（自建 HTTP 后端，作者注明后端上 HTTPS 后改配置）
- 凭证安全：CredentialCipher（用户口令派生密钥 AES-GCM），Android Keystore / 桌面 credential.key 本地密钥文件；认证备份文件可导出换机恢复
- 浏览器扩展「甘露解析下载助手」（MV3）：service_worker 拦截/接管浏览器下载，权限 downloads/webRequest/cookies/contextMenus/scripting，通过 `http://127.0.0.1` 回环接口对接桌面主程序（REA 应用图：3 个 JS、16 条请求关系、8 类事件，证据已留存）

## 四、免登录/账号门槛画像

| 功能 | 是否需登录 |
|---|---|
| 链接识别/提取码匹配 | 免登录（纯本地正则） |
| 网盘分享浏览+取直链 | 需**对应网盘**的账号 Cookie/JWT（转存取链型平台）；蓝奏云系分享页解析基本免登录 |
| 视频解析 | 抖音/小红书/快手/微博/AcFun 免登录直出；B 站登录才有高清；Pixiv 免登录仅部分公开作品 |
| P2P/直链下载 | 免登录（本地引擎） |
| 甘露解析自身 | **无任何账号体系**——没有会员/积分/云备份，与 Voyage 形成鲜明对比 |

## 五、协议边界（★2026-11-07 已更新）

甘露解析原协议为 AGPL-3.0。**2026-11-07 用户与甘露解析作者沟通后获口头授权「随便搞」**——因此直接采用 LGAnalysis 源码为基线做二次开发（改造见 11-07 commit 68d96cb），不再走"只参考规格独立实现"路线。注意：授权系用户口头转述，未落纸；若日后需要书面授权或更换路线，再议。

另注意各网盘解析涉及平台风控（百度被上游标注高风险）；对外文案按 [[feedback-user-visible-only-our-brand]] 处理，不出现甘露解析/上游仓库名。

## 六、对甘露解析（LG Analysis）的设计建议

1. **沿用四件套适配器模式**：每网盘 Api/Constants/AccountRepo/ResolveRepo 一组 + ShareLinkParser 单入口正则族，新平台即插即用
2. **下载中台**：Range 分片并发 + 弹性区分配 + .plan 断点续传 + 全局限速统一管所有来源；P2P 走外挂引擎（Gopeed 思路：内核可云端按架构下发，主程序不内置）
3. **账号多形态**：Cookie 型（WebView/内嵌浏览器+本机浏览器导入）与账密/JWT 型并存；凭证口令派生 AES-GCM 本地加密+可导出备份
4. **提取码本地匹配**：URL 参数+文案正则即可，不必上云端码库
5. **B 站类分轨内容**：自实现分片 MP4 重封装（参考其 tfhd/tfdt 处理思路），不引 ffmpeg
6. **更新/公告通道**：GitHub Releases + 镜像前缀 + 独立公告 JSON——与既有发布规范（发布动作归用户）吻合

## 七、产物与证据

- 本报告：D:\Agent\LGAnalysis\01-甘露解析LGAnalysis源码分析报告.md
- Voyage 报告（前参考物，留档）：00-参考软件逆向报告-Voyage.md（其「网盘解析」悬案由本轮 LGAnalysis 完整解答）
- 图标集：D:\Agent\icon\LGAnalysis-icons（金露滴+刻印放大镜，生成脚本 research/gen_lganalysis_icon.py）
- 源码解包（临时）：D:\Agent\_tmp\yunx\（阅读完成后删除，原始 zip 保留在 example/ 可随时重解）
