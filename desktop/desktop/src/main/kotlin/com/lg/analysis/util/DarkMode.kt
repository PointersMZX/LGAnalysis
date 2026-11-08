package com.lg.analysis.util

import com.sun.jna.Function
import com.sun.jna.Library
import com.sun.jna.Native
import com.sun.jna.Pointer
import com.sun.jna.WString
import com.sun.jna.platform.win32.Advapi32Util
import com.sun.jna.platform.win32.Kernel32
import com.sun.jna.platform.win32.WinReg

/**
 * 原生菜单配色桥接层。
 *
 * 目标配色由**系统「应用」颜色模式**决定（读注册表 AppsUseLightTheme），不写死：
 * 深色 → uxtheme 的 ForceDark，浅色 → ForceLight。启动时应用一次，
 * 每次弹菜单前再 [refresh] 一次，这样运行中切换系统配色也能跟着变。
 *
 * native/darkmode.dll 负责实际调用（uxtheme.dll 序号 132/135/136）。
 * 注意：JNA 的 Native.load 不读取 java.library.path，所以这里必须用 System.loadLibrary。
 *
 * 若构建环境没有 C++ 编译器、darkmode.dll 缺失，则回落到 [DirectUx]：
 * 由 JNA 直调 uxtheme 同款序号（135/132/136），行为与 dll 完全一致。
 */
object DarkMode {

    private const val TAG = "LGAnalysis-DarkMode"
    private const val PERSONALIZE_KEY =
        "Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize"
    private const val APPS_USE_LIGHT_THEME = "AppsUseLightTheme"

    private interface Kernel32Lib : Library {
        fun GetProcAddress(hModule: Pointer, lpProcName: String): Pointer?
    }

    private val k32: Kernel32Lib? by lazy {
        runCatching { Native.load("kernel32", Kernel32Lib::class.java) }.getOrNull()
    }

    /** darkmode.dll 导出的 EnableDarkMode(int dark)；null 表示该层不可用（菜单保持默认配色） */
    private val enableFn: Function? by lazy {
        runCatching {
            System.loadLibrary("darkmode")
            val module = Kernel32.INSTANCE.GetModuleHandle("darkmode.dll")
                ?: run {
                    Log.w(TAG, "GetModuleHandle(darkmode.dll) 返回 null")
                    return@runCatching null
                }
            val addr = k32?.GetProcAddress(module.pointer, "EnableDarkMode")
                ?: run {
                    Log.w(TAG, "GetProcAddress(EnableDarkMode) 返回 null")
                    return@runCatching null
                }
            Function.getFunction(addr, Function.ALT_CONVENTION)
        }.onFailure {
            Log.w(TAG, "加载 darkmode.dll 失败: ${it.message}")
        }.getOrNull()
    }

    /** JNA 直调兜底：darkmode.dll 缺失时直接调 uxtheme 序号（135/132/136），与 dll 行为一致 */
    private class DirectUx {
        private interface OrdK32 : Library {
            fun LoadLibraryW(name: WString): Pointer?

            // 序号调用：第 2 参带 0x8000 高位（x64 调用方零扩展，int 传 32900/32903/32904 即 0x8084/0x8087/0x8088）
            fun GetProcAddress(hModule: Pointer, ordinal: Int): Pointer?
        }

        private val k32 = Native.load("kernel32", OrdK32::class.java)
        // 与 darkmode.cpp 一致：不 FreeLibrary，避免卸载后 SetPreferredAppMode 状态丢失
        private val module = k32.LoadLibraryW(WString("uxtheme.dll"))
            ?: throw IllegalStateException("uxtheme.dll 加载失败")

        private fun fn(ordinal: Int): Function {
            val addr = k32.GetProcAddress(module, ordinal or 0x8000)
                ?: throw IllegalStateException("GetProcAddress 序号 $ordinal 返回 null")
            return Function.getFunction(addr)
        }

        fun apply(dark: Boolean) {
            val empty = arrayOf<Any>()
            fn(135).invoke(Void.TYPE, arrayOf<Any>(if (dark) 2 else 3)) // SetPreferredAppMode
            fn(132).invoke(Void.TYPE, empty)                           // RefreshImmersiveColorPolicyState
            fn(136).invoke(Void.TYPE, empty)                            // FlushMenuThemes
        }
    }

    private val directUx: DirectUx? by lazy {
        runCatching { DirectUx() }.onFailure {
            Log.w(TAG, "JNA 直调层初始化失败: ${it.message}")
        }.getOrNull()
    }

    /** 系统「应用」是否为深色；读不到按浅色（等同系统默认） */
    private fun systemUsesDark(): Boolean = runCatching {
        Advapi32Util.registryGetIntValue(
            WinReg.HKEY_CURRENT_USER, PERSONALIZE_KEY, APPS_USE_LIGHT_THEME
        ) == 0
    }.getOrDefault(false)

    /** 启动时调用一次（需在任何窗口创建之前） */
    fun enable() {
        if (!isWindows()) return
        val dark = systemUsesDark()
        Log.i(TAG, "system app theme = " + if (dark) "dark" else "light")
        apply(dark)
    }

    /** 按当前系统配色重新应用；菜单弹出前调用，跟随运行中的配色变化 */
    fun refresh() {
        if (!isWindows()) return
        apply(systemUsesDark())
    }

    private fun apply(dark: Boolean) {
        val fn = enableFn
        if (fn != null) {
            runCatching { fn.invoke(Void.TYPE, arrayOf<Any>(if (dark) 1 else 0)) }
                .onFailure { Log.w(TAG, "apply dark=$dark failed: ${it.message}") }
        } else {
            directUx?.let {
                runCatching { it.apply(dark) }
                    .onFailure { e -> Log.w(TAG, "JNA 直调 apply dark=$dark failed: ${e.message}") }
            } ?: Log.w(TAG, "菜单配色层不可用（darkmode.dll 缺失且 JNA 兜底初始化失败），菜单保持默认配色")
        }
    }

    private fun isWindows() = System.getProperty("os.name", "").lowercase().contains("win")
}
