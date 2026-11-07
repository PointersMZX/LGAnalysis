"""LGTOOLS 甘露工具箱 图标集生成器 v2（紫底金框 + 金色露滴内凹扳手）"""
import math
import os
from PIL import Image, ImageDraw, ImageFilter, ImageChops

OUT = r"D:\Agent\icon\LGTOOLS-icons"
S = 2048

GOLD_LIGHT = (248, 226, 156)
GOLD_MID = (233, 193, 100)
GOLD_DEEP = (172, 122, 42)
PLATE_TOP = (44, 32, 66)
PLATE_BOT = (24, 17, 38)
ENGRAVE = (26, 18, 42)
BORDER = (216, 172, 84)


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
    x = mt**3 * p0[0] + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0]
    y = mt**3 * p0[1] + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1]
    return (x, y)


def droplet_points(cx, top, R, cyb, n=120):
    """标准水滴轮廓：尖顶 + 两侧贝塞尔 + 底部半圆"""
    pts = []
    # 左侧曲线：尖顶 -> 左腰（底切点，切线竖直）
    p0 = (cx, top)
    p1 = (cx - 130, top + 150)
    p2 = (cx - R, cyb - R * 0.55)
    p3 = (cx - R, cyb)
    for i in range(n):
        pts.append(cubic(p0, p1, p2, p3, i / (n - 1)))
    # 底部半圆（180° -> 0°，经底部）
    for a in range(180, -1, -1):
        rad = math.radians(a)
        pts.append((cx + R * math.cos(rad), cyb + R * math.sin(rad)))
    # 右侧曲线镜像回来
    for i in range(n):
        t = i / (n - 1)
        p0r = (cx, top)
        p1r = (cx + 130, top + 150)
        p2r = (cx + R, cyb - R * 0.55)
        p3r = (cx + R, cyb)
        pts.append(cubic(p3r, p2r, p1r, p0r, 1 - t))
    return pts


def make_wrench(size, center, length, shaft_w, head_r, dark):
    """经典开口扳手（正置，竖直），返回 RGBA 图层"""
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy = center
    half = length // 2
    # 杆
    d.rounded_rectangle([cx - shaft_w // 2, cy - half + head_r, cx + shaft_w // 2, cy + half - head_r * 0.7],
                        radius=shaft_w // 2, fill=dark + (255,))
    # 上头：圆环 + 顶部矩形缺口
    d.ellipse([cx - head_r, cy - half, cx + head_r, cy - half + 2 * head_r], fill=dark + (255,))
    # 下头
    hr2 = int(head_r * 0.85)
    d.ellipse([cx - hr2, cy + half - hr2, cx + hr2, cy + half + hr2], fill=dark + (255,))
    return layer


def punch_notches(layer, center, length, head_r):
    """在扳手图层上按角度抠出开口（用透明多边形）"""
    cx, cy = center
    half = length // 2
    notch_w = int(head_r * 0.52)
    d = ImageDraw.Draw(layer)
    # 上开口（从上方进入头心）
    d.polygon([(cx - notch_w, cy - half - head_r * 0.2),
               (cx + notch_w, cy - half - head_r * 0.2),
               (cx + notch_w * 0.55, cy - half + head_r * 1.15),
               (cx - notch_w * 0.55, cy - half + head_r * 1.15)], fill=(0, 0, 0, 0))
    # 下开口
    hr2 = int(head_r * 0.85)
    d.polygon([(cx - notch_w * 0.9, cy + half + hr2 * 1.2),
               (cx + notch_w * 0.9, cy + half + hr2 * 1.2),
               (cx + notch_w * 0.5, cy + half - hr2 * 0.6),
               (cx - notch_w * 0.5, cy + half - hr2 * 0.6)], fill=(0, 0, 0, 0))
    return layer


def sparkle(color, r):
    img = Image.new("RGBA", (r * 2 + 8, r * 2 + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = r + 4
    f = 0.18
    pts = [(c, 4), (c + r * f, c - r * f), (c + r, c), (c + r * f, c + r * f),
           (c, c + r), (c - r * f, c + r * f), (c - r, c), (c - r * f, c - r * f)]
    d.polygon(pts, fill=color)
    return img


def main():
    for sub in ("source", "png", "bmp", "ico"):
        os.makedirs(os.path.join(OUT, sub), exist_ok=True)

    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    pad, radius = 190, 430
    plate_box = [pad, pad, S - pad, S - pad]

    # 金色外发光
    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    dg = ImageDraw.Draw(glow)
    dg.rounded_rectangle(plate_box, radius=radius, outline=(242, 200, 116, 210), width=24)
    glow = glow.filter(ImageFilter.GaussianBlur(52))
    img.alpha_composite(glow)

    # 紫渐变底板
    plate = vertical_gradient((S, S), PLATE_TOP, PLATE_BOT).convert("RGBA")
    mask_img = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask_img).rounded_rectangle(plate_box, radius=radius, fill=255)
    img.paste(plate, (0, 0), mask_img)

    # 装饰暗圆
    deco = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    dd = ImageDraw.Draw(deco)
    dd.ellipse([pad + 120, S - pad - 320, pad + 280, S - pad - 160], fill=(31, 22, 50, 255))
    dd.ellipse([S - pad - 280, pad + 320, S - pad - 170, pad + 430], fill=(31, 22, 50, 255))
    img.alpha_composite(Image.composite(deco, Image.new("RGBA", (S, S), (0, 0, 0, 0)), mask_img))

    # 金色描边
    border = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(border).rounded_rectangle(plate_box, radius=radius, outline=BORDER + (255,), width=20)
    img.alpha_composite(border)

    # ===== 主图形：金色露滴 + 内凹扳手 =====
    cx, cy = S // 2, S // 2
    top, R, cyb = cy - 400, 330, cy + 120

    glyph = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(glyph)
    d.polygon(droplet_points(cx, top, R, cyb), fill=GOLD_MID + (255,))

    # 渐变着色
    grad = vertical_gradient((S, S), GOLD_LIGHT, GOLD_DEEP).convert("RGBA")
    glyph = Image.composite(grad, glyph, glyph.split()[3])

    # 左上高光
    hl = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    dh = ImageDraw.Draw(hl)
    dh.ellipse([cx - 210, cy - 180, cx - 60, cy - 30], fill=(255, 248, 220, 150))
    hl = hl.filter(ImageFilter.GaussianBlur(36))
    glyph.alpha_composite(hl)

    # 内凹扳手：浅金偏移层（右下浮雕亮边）-> 深色刻印扳手
    wc = (cx, cy + 40)
    wl_off = make_wrench((S, S), (wc[0] + 12, wc[1] + 12), length=760, shaft_w=96, head_r=118, dark=(214, 172, 88))
    wl_off = punch_notches(wl_off, (wc[0] + 12, wc[1] + 12), length=760, head_r=118)
    wl_off = wl_off.rotate(45, center=wc, resample=Image.BICUBIC)
    wl = make_wrench((S, S), wc, length=760, shaft_w=96, head_r=118, dark=ENGRAVE)
    wl = punch_notches(wl, wc, length=760, head_r=118)
    wl = wl.rotate(45, center=wc, resample=Image.BICUBIC)
    glyph.alpha_composite(wl_off)
    glyph.alpha_composite(wl)

    # 投影
    sh = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([cx - 240, cyb + R - 30, cx + 240, cyb + R + 110], fill=(0, 0, 0, 110))
    sh = sh.filter(ImageFilter.GaussianBlur(50))
    img.alpha_composite(sh)
    img.alpha_composite(glyph)

    # 四芒星（右上）
    sp = sparkle((250, 228, 152, 255), 92)
    img.alpha_composite(sp, (S - pad - 360, pad + 150))

    final = img.resize((1024, 1024), Image.LANCZOS)
    final.save(os.path.join(OUT, "source", "LGTOOLS-violet-1024.png"))

    sizes = [16, 24, 32, 48, 64, 128, 256, 512]
    for s in sizes:
        final.resize((s, s), Image.LANCZOS).save(os.path.join(OUT, "png", f"{s}x{s}.png"))
        final.resize((s, s), Image.LANCZOS).convert("RGB").save(os.path.join(OUT, "bmp", f"{s}x{s}.bmp"))
    final.resize((256, 256), Image.LANCZOS).save(os.path.join(OUT, "ico", "app.ico"),
                                                 format="ICO", sizes=[(256, 256)])
    print("done")


if __name__ == "__main__":
    main()
