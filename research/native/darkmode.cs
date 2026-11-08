// 替代 C++ 编译 darkmode.dll 的本机方案（无 MSVC/g++ 时用 csc 编混合模式程序集）
// 导出 EnableDarkMode(int dark)：与 native/darkmode.cpp 行为一致
using System;
using System.Runtime.InteropServices;

public static class DarkModeExport
{
    [DllImport("uxtheme.dll", EntryPoint = "#135", CharSet = CharSet.Ansi)]
    private static extern int SetPreferredAppMode(int mode);

    [DllImport("uxtheme.dll", EntryPoint = "#132")]
    private static extern void RefreshImmersiveColorPolicyState();

    [DllImport("uxtheme.dll", EntryPoint = "#136")]
    private static extern void FlushMenuThemes();

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern IntPtr LoadLibrary(string name);

    [Export("EnableDarkMode", CallingConvention = CallingConvention.Cdecl)]
    public static void EnableDarkMode(int dark)
    {
        // 与 C++ 版一致：借 LoadLibrary 取序号地址后【绝不 FreeLibrary】，
        // 否则启动早期会把 uxtheme 卸载，PreferredAppMode 状态丢失
        IntPtr h = LoadLibrary("uxtheme.dll");
        if (h == IntPtr.Zero) return;
        SetPreferredAppMode(dark != 0 ? 2 : 3);
        RefreshImmersiveColorPolicyState();
        FlushMenuThemes();
    }
}
