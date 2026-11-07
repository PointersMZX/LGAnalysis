# 甘露解析（LG Analysis）前期准备 —— 参考软件 Voyage 逆向报告（留档）

> 日期：2026-11-06　|　性质：内部开发文档（可记录参考物来源）
> 参考资料位置：D:\Agent\example\3（无源码，二进制逆向）
> ★2026-11-07 项目更名「甘露解析（LG Analysis）」，主参考物已换为云析 YunX（见 01-云析YunX源码分析报告.md）；本报告留档。
> 本报告结论均来自静态逆向取证（字符串/元数据/程序集/资产目录），未运行目标程序，未做动态行为验证。

---

## 一、参考软件身份认定

| 项 | 桌面端 | Android 端 |
|---|---|---|
| 文件 | Voyage-Setup-0.1.2-alpha-win-x64.exe（97MB） | voyage-release-1.0.22-alpha.01-arm64-v8a.apk（162MB） |
| 包名/版本 | 程序集 Voyage 0.1.2.0（.NET 10） | com.cityray.aihrplus.vgjx（应用名「Voyage 工具箱」，versionCode 1002201） |
| 技术栈 | **Avalonia UI + Semi.Avalonia/Ursa 主题 + .NET 10 自包含**，非 Electron | 原生 Android，14 个 dex，内嵌 QuickJS（libqjs）、Aria2（libaria2c）、mpv 系播放（libttmplayer_lite）、本地 AI（LiteRT/ONNX）、高德地图 SDK |
| 安装器 | 非 NSIS/Inno：PE 外壳 + 内嵌 ZIP（293 文件，偏移 0x15ACFED 处直接切出） | — |
| 账号体系 | 自研 Aegis 服务端客户端（Voyage.Aegis.dll，域名占位 aegis.example.com，上线时替换） | 同族账号 + 大量广告/变现 SDK（sigmob、广点通、百度、优量汇 zj.zjsdk） |
| 源码 | GitHub MiChongs/Voyage 已 404（曾经存在），确认无公开源码 | 同上 |

两个端是同一产品家族：桌面端偏「影音工具箱」，Android 端是「大而全超级工具箱」。

## 二、桌面端功能全景（来自视图清单 + 工具注册表字符串）

主程序 Voyage.dll（5.7MB，1613 类型/17826 方法），工具注册表自带官方描述（原文摘录）：

**纯本地小工具（8 件）**
1. **Base64 编解码** — 文本与 Base64 快速转换
2. **时间戳转换** — Unix 时间戳与本地时间互转（秒/毫秒/日期串）
3. **ID 生成器** — 批量生成 v4 随机或 v7 有序 UUID
4. **密码生成器** — 生成指定长度的安全随机密码
5. **JSON 工具箱** — 格式化、压缩与语法校验
6. **哈希校验** — 文本或文件的 MD5、SHA-1、SHA-2 摘要
7. **图片工具箱** — PNG/JPEG/WebP 互转、按质量压缩、保存或复制
8. **身份验证器（TOTP）** — 二维码导入，与 Google Authenticator 互相导出（含 otpauth-migration 导入导出）

**影音大模块（5 件）**
9. **短剧** — 聚合红果、河马等**二十个来源**，连续播放、追剧更新
10. **下载管理器** — 多线程分块下载、HLS(m3u8) 合并、全局与单任务限速（256KB/s~50MB/s+不限速档）、断点续传、失效链接自动换新，统一管理各工具下载
11. **视频解析** — 抖音/哔哩哔哩/TikTok 等**五十余个平台**，取无水印视频/实况/原声，支持 yt-dlp 通用解析与批量下载
12. **音乐** — **五个音源**搜索与播放、榜单与歌单广场、逐字歌词、各平台歌单导入与无损下载（支持导入自定义音源：字符串含「音源密钥无效/音源地址无效」）
13. **追番** — 聚合 AniCh、樱花等**六十余个番剧片源**、放送表、索引与排行、弹幕、显卡超分辨率（RtxVideo 模块，NVDEC/VAAPI/D3D11VA 硬解、mpv 播放内核）

**智能/账号（2 类）**
14. **口味画像/本地推荐** — models/text/model_int8.onnx + vocab.txt：本机文本分类模型，按收听行为生成画像，明示「不上传任何数据」
15. **账号体系（Aegis）** — 登录/注册（密码、二维码、WebAuthn、短信、OAuth、Passkey、卡密）、2FA、签到送积分、积分/经验等级、会员（试用/永久/钱包/支付：Lemon Squeezy、Coinbase、京东等）、云备份、消息通知、登录设备管理、**功能时长租约（/features/time/leases）**、更新发布通道（/releases）

**壳层**：工具坞（ToolDockWindow 独立小窗）、系统托盘、开机自启（Linux .desktop/Windows）、暗色玻璃风主题、单实例。

## 三、★免登录可用的免费功能清单（本次核心交付）

**结论：桌面端除「账号功能」外，全部工具与影音功能均可不登录直接使用。**
未发现任何「请先登录后使用」的全局门控字符串；会员/积分/签到均为增值功能而非功能开关。

### 3.1 完全免登录（纯本地，零网络依赖）
- Base64 编解码、时间戳转换、UUID/ID 生成器、密码生成器、JSON 工具箱、哈希校验（文本+文件）、图片工具箱（格式转换/压缩）
- 身份验证器 TOTP（本地密钥计算 + 二维码导入导出，全部本地完成）

### 3.2 免登录（走公开接口，无需任何账号）
- **追番**：片源=苹果 CMS vod 开放接口（暴风/iKun/魔都/无尽/极速/光速/红牛/新浪等资源站），Bangumi(bgm.tv) 资料、放送表、排行；弹幕来自 danmuzf 公共弹幕服。仅个别源（AniCh 部分剧集）需要该源自己的账号，游客画质受限 360P
- **短剧**：二十个来源中绝大多数为开放采集接口（红果 hongguoduanju.com、番茄短剧 fqnovel 系、xgshort 有 guest-login 游客令牌机制=自动免登录、芒果 damang、9ddm、qmplaylet 等）
- **视频解析**：五十余个平台链接解析（含 yt-dlp 通用兜底）；仅年龄限制视频需平台自身登录（提示语内置于解析器）
- **音乐**：搜索/播放/榜单走音源（支持外挂音源导入），本地歌单/逐字歌词/下载不依赖 Voyage 账号
- **下载管理器**：多线程/限速/断点续传/m3u8 合并，与账号无关；限速档位是用户自选设置（含「不限速」），并非会员专属

### 3.3 需要登录（Aegis 账号）的功能——甘露工具箱可自选是否做
- 签到/积分/经验等级、会员开通与钱包支付、卡密兑换、云备份（CloudBackup）、消息通知、多设备登录管理、功能时长租约、试用会员领取

### 3.4 Android 端补充（功能目录来自 assets 一级目录，共 50+ 小功能）
证件照 idphoto、八字 bazi、BMI、垃圾分类 garbage、金价 goldprice、油价 oilprice、天气 weather、白噪音 whitenoise、钢琴 piano、铁路 railway、景区 scenic、限行 traffic_limit、小说 novel（含 JsExtensions 书源引擎，类阅读/Legado）、漫画 comic、杂志 magazine、听歌识曲 music_recognize、多线 ping multiping、地图 maplibre、OCR(mlkit)、小游戏（马里奥/魔塔/恐龙/合成水果/坦克/跑酷/retrogame）等。Android 端广告 SDK 密集，变现重；本报告以桌面端为主要参考。

## 四、数据源端点清单（直接可复用素材）

**追番/短剧（苹果 CMS vod 协议 api.php/provide/vod）**：bfzyapi.com、ikunzyapi.com、mdzyapi.com、moduzy.com、wujinapi.{me,com,net}、jszyapi.com、guangsuapi.com、hongniuzy2/3.com、xinlangapi.com、souavzy.vip、hsckzy888.com、naixxzy.com、apidanaizi.com、xingba111.com、slapibf.com、jkunzyapi.com、rycjapi.com、rytvapi.com、cttv.vip、ysxq.cc、xgzyapi.com、1080zyku.com、yzzy-api.com、yyzy-tv.vip、lziapi.com、lzcaiji.com、dyttzyapi.com（另有 360资源/爱奇艺资源站条目）
**短剧专属**：hongguoduanju.com（分类/排行/搜索/详情/联想）、api-store.qmplaylet.com、api-read.qmplaylet.com、api.drama.9ddm.com、m.xgshort.com（guest-login+episodes+query）、fqnovel 短剧 api5-normal-*、百度好看 playlet、mgtv damang
**番剧资料/弹幕/播放**：bgm.tv、danmuzf.vip、aniplayer.pgon（punycode 域）、haho.moe 等
**视频解析平台**：抖音/iesdouyin、哔哩哔哩、快手/ Kwai、小红书、微博、TikTok、Tumblr、Pinterest、梨视频、头条、AcFun、网易云音乐、酷我、QQ音乐等 50+ 域名规则（详见 research/strings/Voyage.VideoParse.dll.strings.txt）
**完整原始字符串证据**：`research/strings/*.strings.txt`（按程序集分文件，UTF-16 全量抽取）

## 五、对甘露工具箱的可借鉴设计

1. **工具注册表模式**：ToolId + Descriptor + 工厂 Create + Packs 打包开关（`未知的工具 {ToolId}` 兜底），新工具即插即用；工具坞独立小窗 + 最近使用
2. **下载中台**：所有模块共用一个下载管理器（多线程分块+m3u8 合并+断点续传+失效自动换源+统一限速），这是各模块体验一致性的关键件
3. **音源外挂**：音源以外部配置/脚本形式导入（密钥/地址校验），应用本体不带任何抓取逻辑——与我们音乐/影视线既有方案同构
4. **账号可选化**：核心功能不挂登录墙；账号体系（签到/积分/会员/云备份）整体封装为可选服务端模块，未配置时界面隐藏（字符串「Aegis 未配置」证实该开关存在）
5. **本地 AI 画像**：ONNX int8 小模型 + 词表做口味标签，全程本机，作为隐私卖点
6. **更新通道**：自建 /releases 检查（发布/渠道/变更日志结构化）——注意与我们的「发布归用户」规范衔接

## 五A、专项补充：「网盘解析」排查（2026-11-06 二轮）

结论先行：**手头这两个安装包里没有可静态还原的「网盘解析」实现**，证据如下：

1. **桌面 0.1.2-alpha：整个功能不存在。** 三层证据全零：全部 15 个程序集的 UTF-16 代码串、UTF-8 字节、内嵌托管资源（Voyage.dll 资源段 1.2MB=纯编译后 XAML 视图）中「网盘/提取码/分享链接/直链」均 0 命中。网盘解析应为后续版本新增。
2. **Android 1.0.22-alpha：只有功能入口，没有文案与实现痕迹。** resources.arsc 全量 3.2 万条中文文案中，网盘家族仅 2 条：`string/pan_search_share_label`＝「网盘搜索 / Drive Search」、`string/pan_search_share_empty`（搜索无结果提示）。「网盘解析」字样在资源表与 dex 中均不存在。
3. **Android 代码层字符串被选择性加密**：健全性检查显示 `https`/`.com` 等库字符串为明文，但 `bilibili`/`douyin`/中文功能词全部 0 命中（同批功能词在 resources.arsc 里有），即业务字符串在运行时解密。静态拿不到网盘解析的站点规则与接口，需要动态调试（frida + 真机/模拟器跑起来 hook 解密后的字符串/网络层）或获取更新的安装包才能还原。
4. 顺带澄清的周边发现：assets/lanshare＝「Voyage 共享」局域网文件共享 PWA（同一局域网浏览/下载/上传），不是蓝奏云；解析家族文案只有视频解析/短视频解析/yt-dlp/AI 解析；AI 解析命中阿里 DashScope 国际端点（dashscope-intl.aliyuncs.com）；全包无 WebDAV/Alist/挂载/秒传类能力。

**对甘露工具箱的意义**：若要做网盘解析，参考物上无现成规则可抄，需要自行设计（或走「音源/解析规则外挂」路线让规则可远程更新）；动态逆向 Voyag 网盘解析可作为后续单独立项（需模拟器+frida 环境）。



- 图标集：`D:\Agent\icon\LGTOOLS-icons\`（source 1024 / png 八档 / bmp 八档 / ico 单条目 PNG，生成脚本 `research/gen_lgtools_icon.py`）
- 字符串证据：`research/strings/`（桌面 15 个程序集 + Android dex）
- 原始解包（临时，用后即删）：`D:\Agent\_tmp\lgtools-re\`
- 未做事项（明确留空）：未运行程序做动态验证；未解 Android resources.arsc 全量文案；未抠 50+ 解析平台的具体正则（后续开发时按需从 VideoParse 程序集细挖）
