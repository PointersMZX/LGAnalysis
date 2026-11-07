"""甘露解析（LG Analysis）图标集生成器（紫底金框 + 金露滴 + 刻印放大镜）"""
import math
import os
from PIL import Image, ImageDraw, ImageFilter

OUT = r"D:\Agent\icon\LGAnalysis-icons"
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
    pts = []
    p0, p1 = (cx, top), (cx - 130, top + 150)
    p2, p3 = (cx - R, cyb - R * 0.55), (cx - R, cyb)
    for i in range(n):
        pts.append(cubic(p0, p1, p2, p3, i / (n - 1)))
    for a in range(180, -1, -1):
        rad = math.radians(a)
        pts.append((cx + R * math.cos(rad), cyb + R * math.sin(rad)))
    for i in range(n):
        t = i / (n - 1)
        p0r, p1r = (cx, top), (cx + 130, top + 150)
        p2r, p3r = (cx + R, cyb - R * 0.55), (cx + R, cyb)
        pts.append(cubic(p3r, p2r, p1r, p0r, 1 - t))
    return pts


def make_magnifier(size, cx, cy, ring_r, stroke, handle_len, color):
    """正置放大镜：圆环 + 右下手柄（rotate 前的母版）"""
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse([cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r],
              outline=color + (255,), width=stroke)
    # 手柄：粗圆角杆，从环右下沿向外
    ang = math.radians(45)
    hx0 = cx + ring_r * math.cos(ang)
    hy0 = cy + ring_r * math.sin(ang)
    hx1 = cx + (ring_r + handle_len) * math.cos(ang)
    hy1 = cy + (ring_r + handle_len) * math.sin(ang)
    d.line([hx0, hy0, hx1, hy1], fill=color + (255,), width=int(stroke * 1.7))
    d.ellipse([hx1 - stroke * 0.85, hy1 - stroke * 0.85,
               hx1 + stroke * 0.85, hy1 + stroke * 0.85], fill=color + (255,))
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

    glow = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(glow).rounded_rectangle(plate_box, radius=radius, outline=(242, 200, 116, 210), width=24)
    img.alpha_composite(glow.filter(ImageFilter.GaussianBlur(52)))

    plate = vertical_gradient((S, S), PLATE_TOP, PLATE_BOT).convert("RGBA")
    mask_img = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask_img).rounded_rectangle(plate_box, radius=radius, fill=255)
    img.paste(plate, (0, 0), mask_img)

    deco = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    dd = ImageDraw.Draw(deco)
    dd.ellipse([pad + 120, S - pad - 320, pad + 280, S - pad - 160], fill=(31, 22, 50, 255))
    dd.ellipse([S - pad - 280, pad + 320, S - pad - 170, pad + 430], fill=(31, 22, 50, 255))
    img.alpha_composite(Image.composite(deco, Image.new("RGBA", (S, S), (0, 0, 0, 0)), mask_img))

    border = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(border).rounded_rectangle(plate_box, radius=radius, outline=BORDER + (255,), width=20)
    img.alpha_composite(border)

    # ===== 主图形：金露滴 + 刻印放大镜（镜心即露滴，透视感）=====
    cx, cy = S // 2, S // 2 - 10
    top, R, cyb = cy - 400, 310, cy + 100

    glyph = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(glyph).polygon(droplet_points(cx, top, R, cyb), fill=GOLD_MID + (255,))
    grad = vertical_gradient((S, S), GOLD_LIGHT, GOLD_DEEP).convert("RGBA")
    glyph = Image.composite(grad, glyph, glyph.split()[3])

    hl = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(hl).ellipse([cx - 200, cy - 190, cx - 60, cy - 50], fill=(255, 248, 220, 150))
    glyph.alpha_composite(hl.filter(ImageFilter.GaussianBlur(36)))

    # 放大镜：镜环完整罩住露滴，手柄伸向右下
    mcx, mcy = cx - 20, cy - 20
    ring_r, stroke = 452, 54
    # 浮雕亮边（偏移 8px，收在环内侧为主）
    mg_off = make_magnifier((S, S), mcx + 8, mcy + 8, ring_r, stroke, 275, (214, 172, 88))
    mg = make_magnifier((S, S), mcx, mcy, ring_r, stroke, 275, ENGRAVE)
    glyph.alpha_composite(mg_off)
    glyph.alpha_composite(mg)
    # 镜内高光弧
    arc = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(arc).arc([mcx - ring_r + stroke, mcy - ring_r + stroke,
                             mcx + ring_r - stroke, mcy + ring_r - stroke],
                            start=190, end=260, fill=(255, 246, 214, 130), width=30)
    glyph.alpha_composite(arc.filter(ImageFilter.GaussianBlur(10)))

    sh = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([cx - 240, cyb + R - 30, cx + 240, cyb + R + 110], fill=(0, 0, 0, 110))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(50)))
    img.alpha_composite(glyph)

    sp = sparkle((250, 228, 152, 255), 92)
    img.alpha_composite(sp, (S - pad - 360, pad + 150))

    final = img.resize((1024, 1024), Image.LANCZOS)
    final.save(os.path.join(OUT, "source", "LGAnalysis-violet-1024.png"))

    sizes = [16, 24, 32, 48, 64, 128, 256, 512]
    for s in sizes:
        final.resize((s, s), Image.LANCZOS).save(os.path.join(OUT, "png", f"{s}x{s}.png"))
        final.resize((s, s), Image.LANCZOS).convert("RGB").save(os.path.join(OUT, "bmp", f"{s}x{s}.bmp"))
    final.resize((256, 256), Image.LANCZOS).save(os.path.join(OUT, "ico", "app.ico"),
                                                 format="ICO", sizes=[(256, 256)])
    print("done")


if __name__ == "__main__":
    main()
