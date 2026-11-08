# -*- coding: utf-8 -*-
"""双端启动图标替换为甘露解析（露滴+刻印放大镜）"""
import os
import shutil
from PIL import Image, ImageDraw, ImageFilter

ICONS = r"D:\Agent\icon\LGAnalysis-icons"
ROOT = r"D:\Agent\LGAnalysis"

GOLD_LIGHT = (248, 226, 156)
GOLD_MID = (233, 193, 100)
GOLD_DEEP = (172, 122, 42)
PLATE_TOP = (44, 32, 66)
PLATE_BOT = (24, 17, 38)
ENGRAVE = (26, 18, 42)
VIOLET = "#241A38"


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def vertical_gradient(size, top, bot):
    w, h = size
    col = Image.new("RGB", (1, h))
    px = col.load()
    for y in range(h):
        px[0, y] = lerp(top, bot, y / max(1, h - 1))
    return col.resize((w, h))


def cubic(p0, p1, p2, p3, t):
    mt = 1 - t
    return (mt**3 * p0[0] + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0],
            mt**3 * p0[1] + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1])


def droplet_points(cx, top, R, cyb, n=120):
    pts = []
    p0, p1, p2, p3 = (cx, top), (cx - 130, top + 150), (cx - R, cyb - R * 0.55), (cx - R, cyb)
    for i in range(n):
        pts.append(cubic(p0, p1, p2, p3, i / (n - 1)))
    for a in range(180, -1, -1):
        rad = __import__("math").radians(a)
        pts.append((cx + R * __import__("math").cos(rad), cyb + R * __import__("math").sin(rad)))
    for i in range(n):
        t = i / (n - 1)
        p0r, p1r, p2r, p3r = (cx, top), (cx + 130, top + 150), (cx + R, cyb - R * 0.55), (cx + R, cyb)
        pts.append(cubic(p3r, p2r, p1r, p0r, 1 - t))
    return pts


def make_magnifier(size, cx, cy, ring_r, stroke, handle_len, color):
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse([cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r], outline=color + (255,), width=stroke)
    ang = __import__("math").radians(45)
    hx0, hy0 = cx + ring_r * __import__("math").cos(ang), cy + ring_r * __import__("math").sin(ang)
    hx1, hy1 = cx + (ring_r + handle_len) * __import__("math").cos(ang), cy + (ring_r + handle_len) * __import__("math").sin(ang)
    d.line([hx0, hy0, hx1, hy1], fill=color + (255,), width=int(stroke * 1.7))
    d.ellipse([hx1 - stroke * 0.85, hy1 - stroke * 0.85, hx1 + stroke * 0.85, hy1 + stroke * 0.85], fill=color + (255,))
    return layer


def glyph_only(size=1024):
    """纯图形（无紫底板）：金露滴 + 刻印放大镜"""
    S = size
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    cx, cy = S // 2, S // 2 - 10
    top, R, cyb = cy - 400, 310, cy + 100
    d = ImageDraw.Draw(img)
    d.polygon(droplet_points(cx, top, R, cyb), fill=GOLD_MID + (255,))
    grad = vertical_gradient((S, S), GOLD_LIGHT, GOLD_DEEP).convert("RGBA")
    img = Image.composite(grad, img, img.split()[3])
    mcx, mcy = cx - 20, cy - 20
    mg = make_magnifier((S, S), mcx, mcy, 452, 54, 275, ENGRAVE)
    img.alpha_composite(mg)
    # 裁到内容包围盒
    bbox = img.getbbox()
    return img.crop(bbox)


def glyph_plate(size=1024):
    """完整紫底板图标（与 LGAnalysis-icons 同款）"""
    src = Image.open(os.path.join(ICONS, "source", "LGAnalysis-violet-1024.png")).convert("RGBA")
    return src.resize((size, size), Image.LANCZOS)


def make_foreground():
    """自适应前景 432px：图形收进中央 66% 安全区"""
    g = glyph_only(1024)
    # 等比缩放到 ~260px 高（安全区直径 285px）
    scale = 285 / max(g.size)
    g = g.resize((int(g.size[0] * scale), int(g.size[1] * scale)), Image.LANCZOS)
    canvas = Image.new("RGBA", (432, 432), (0, 0, 0, 0))
    canvas.alpha_composite(g, ((432 - g.size[0]) // 2, (432 - g.size[1]) // 2))
    return canvas


def circle_mask(im):
    S = im.size[0]
    m = Image.new("L", (S * 4, S * 4), 0)
    ImageDraw.Draw(m).ellipse([0, 0, S * 4 - 1, S * 4 - 1], fill=255)
    m = m.resize((S, S), Image.LANCZOS)
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    out.paste(im, (0, 0), m)
    return out


def main():
    # ---- 桌面 ----
    plate = glyph_plate(512)
    ico_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    plate.resize((256, 256), Image.LANCZOS).save(os.path.join(ROOT, "desktop", "LGAnalysis.ico"),
                                                 format="ICO", sizes=ico_sizes)
    plate.save(os.path.join(ROOT, "desktop", "desktop", "src", "main", "resources", "icon.png"))
    for s in (16, 32, 48, 128):
        shutil.copy(os.path.join(ICONS, "png", f"{s}x{s}.png"),
                    os.path.join(ROOT, "desktop", "browser-extension", "icons", f"icon{s}.png"))

    # ---- Android ----
    res = os.path.join(ROOT, "android", "app", "src", "main", "res")
    glyph_plate(512).save(os.path.join(res, "drawable", "icon.png"))
    make_foreground().save(os.path.join(res, "drawable-nodpi", "ic_launcher_new_foreground.png"))
    # 背景层改紫底
    bg = f'''<?xml version="1.0" encoding="utf-8"?>
<shape xmlns:android="http://schemas.android.com/apk/res/android">
    <solid android:color="{VIOLET}" />
</shape>
'''
    open(os.path.join(res, "drawable", "ic_launcher_background.xml"), "w", encoding="utf8", newline="\n").write(bg)
    # v26 主别名背景：白 → 紫
    p = os.path.join(res, "drawable-v26", "ic_launcher_new.xml")
    s = open(p, encoding="utf8").read()
    s = s.replace('android:drawable="@android:color/white"', 'android:drawable="@drawable/ic_launcher_background"')
    open(p, "w", encoding="utf8", newline="\n").write(s)
    # mipmap-anydpi-v26 两份的前景指向我们的 png
    for name in ("ic_launcher.xml", "ic_launcher_round.xml"):
        p = os.path.join(res, "mipmap-anydpi-v26", name)
        s = open(p, encoding="utf8").read()
        s = s.replace('android:drawable="@drawable/ic_launcher_foreground"',
                      'android:drawable="@drawable/ic_launcher_new_foreground"')
        open(p, "w", encoding="utf8", newline="\n").write(s)
    # 旧版 webp（API 24/25 兜底）
    sizes = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
    for den, s in sizes.items():
        im = glyph_plate(s)
        im.save(os.path.join(res, f"mipmap-{den}", "ic_launcher.webp"), format="WEBP", quality=90)
        circle_mask(im).save(os.path.join(res, f"mipmap-{den}", "ic_launcher_round.webp"), format="WEBP", quality=90)
    # icon2（主题页图标预览用）
    icon2 = os.path.join(res, "drawable", "icon2.png")
    if os.path.exists(icon2):
        glyph_plate(512).save(icon2)
    print("icons done")


if __name__ == "__main__":
    main()
