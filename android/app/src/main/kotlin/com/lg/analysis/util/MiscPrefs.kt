package com.lg.analysis.util

import android.content.Context
import android.content.SharedPreferences

/**
 * 杂项偏好（onboarding_shown / ignored_version 等，与 settings 主偏好分离）。
 *
 * 文件历史上叫 `yunx_prefs`（上游遗留前缀），现统一为 `lganalysis_prefs`。
 * 首次访问时做一次性迁移：把旧文件里的所有值搬进新文件（不覆盖新文件已有值），
 * 再删掉旧文件——保证已安装用户的首启标记/忽略版本不丢，同时彻底清掉上游遗留文件名。
 */
object MiscPrefs {

    private const val NEW = "lganalysis_prefs"
    private const val LEGACY = "yunx_prefs"

    @Volatile
    private var migrated = false

    fun get(context: Context): SharedPreferences {
        val c = context.applicationContext
        if (!migrated) {
            synchronized(this) {
                if (!migrated) {
                    migrateOnce(c)
                    migrated = true
                }
            }
        }
        return c.getSharedPreferences(NEW, Context.MODE_PRIVATE)
    }

    private fun migrateOnce(c: Context) {
        val legacy = c.getSharedPreferences(LEGACY, Context.MODE_PRIVATE)
        val all = legacy.all
        if (all.isNotEmpty()) {
            val target = c.getSharedPreferences(NEW, Context.MODE_PRIVATE)
            val ed = target.edit()
            for ((k, v) in all) {
                if (target.contains(k)) continue
                when (v) {
                    is Boolean -> ed.putBoolean(k, v)
                    is Int -> ed.putInt(k, v)
                    is Long -> ed.putLong(k, v)
                    is Float -> ed.putFloat(k, v)
                    is String -> ed.putString(k, v)
                    else -> ed.putString(k, v.toString())
                }
            }
            ed.apply()
        }
        c.deleteSharedPreferences(LEGACY)
    }
}
