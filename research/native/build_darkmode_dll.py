# -*- coding: utf-8 -*-
"""手工生成 darkmode.dll（PE32+ x64），无 C++ 编译器环境的兜底方案。
导出 EnableDarkMode(int dark)，行为对齐 native/darkmode.cpp：
uxtheme 序号 135(SetPreferredAppMode) / 132(RefreshImmersiveColorPolicyState) / 136(FlushMenuThemes)。
绝不 FreeLibrary（uxtheme 启动早期常驻，避免卸载导致 PreferredAppMode 状态丢失）。
"""
import struct

OUT = r"D:\Agent\LGAnalysis\desktop\desktop\build\native\darkmode.dll"
BASE = 0x140000000
T_VA = 0x1000   # .text
R_VA = 0x2000   # .rdata
D_VA = 0x3000   # .data（IAT）
FA = 0x200      # 文件对齐
HDR_RAW = 0x200 # 头部结束 = 首节 raw 起点


def align_up(v, a):
    return (v + a - 1) & ~(a - 1)


# ---- 迷你 x86-64 汇编器：记录指令相对位移与短跳转，结束时统一回填 ----
class Mini:
    def __init__(self):
        self.b = bytearray()
        self.rip_rel = []   # (disp32 偏移, 目标 RVA)
        self.jumps = []     # (rel8 偏移, 目标标签名)

    def add(self, *ws):
        for w in ws:
            self.b += w

    def call_rip(self, target_rva):
        """call [rip+disp]：FF 15 + disp32（指令共 7 字节，disp 位于 off，下一指令在 off+5）"""
        self.add(b"\xFF\x15")
        off = len(self.b)
        self.rip_rel.append((off, target_rva, 5))
        self.add(b"\x00\x00\x00\x00")

    def lea_rip(self, target_rva):  # 48 8D 0D + disp32（下一指令在 off+4）
        self.add(b"\x48\x8D\x0D")
        off = len(self.b)
        self.rip_rel.append((off, target_rva, 4))
        self.add(b"\x00\x00\x00\x00")

    def jz_short(self, label):
        self.add(b"\x74\x00")
        self.jumps.append((len(self.b) - 1, label))

    def jmp_short(self, label):
        self.add(b"\xEB\x00")
        self.jumps.append((len(self.b) - 1, label))

    def je_short(self, label):
        self.jz_short(label)

    def getproc_call(self, ordinal, iat_getproc_rva):
        """mov rcx, r11 ; mov edx, <ord|0x8000> ; call [GetProcAddress] ; test rax,rax ; jz <fail>"""
        self.add(b"\x48\x89\xD9")                       # mov rcx, r11
        self.add(b"\xBA" + struct.pack("<I", ordinal | 0x8000))  # mov edx, imm
        self.call_rip(iat_getproc_rva)
        self.add(b"\x48\x85\xC0")                       # test rax, rax

    def finalize(self, code_rva, labels):
        for off, target, delta in self.rip_rel:
            disp = target - (code_rva + off + delta)
            struct.pack_into("<i", self.b, off, disp)
        for off, label in self.jumps:
            tgt = labels[label]  # 标签为代码内字节偏移，跳转位移与 code_rva 无关
            struct.pack_into("<b", self.b, off, tgt - (off + 1))


def gen_code(iat_load_rva, iat_getproc_rva, uxtheme_str_rva):
    m = Mini()
    m.add(b"\x48\x83\xEC\x28")                          # sub rsp, 0x28
    m.add(b"\x41\x89\xCE")                               # mov r10d, ecx (dark)
    m.lea_rip(uxtheme_str_rva)                            # lea rcx, "uxtheme"
    m.call_rip(iat_load_rva)                              # LoadLibraryW
    m.add(b"\x48\x85\xC0")                                # test rax, rax
    m.jz_short("done")
    m.add(b"\x4C\x89\xC3")                                # mov r11, rax (保留句柄，绝不 FreeLibrary)

    labels = {}
    labels["set_lp"] = len(m.b)
    m.getproc_call(135, iat_getproc_rva)                  # SetPreferredAppMode
    m.jz_short("refresh_lp")
    m.add(b"\x49\x89\xC0")                                # mov r8, rax
    m.add(b"\x41\x85\xD2")                                # test r10d, r10d
    m.je_short("light")
    m.add(b"\xB9\x02\x00\x00\x00")                        # mov ecx, 2 (ForceDark)
    m.jmp_short("call_set")
    labels["light"] = len(m.b)
    m.add(b"\xB9\x03\x00\x00\x00")                        # mov ecx, 3 (ForceLight)
    labels["call_set"] = len(m.b)
    m.add(b"\x41\xFF\xD0")                                # call r8

    labels["refresh_lp"] = len(m.b)
    m.getproc_call(132, iat_getproc_rva)
    m.jz_short("flush_lp")
    m.add(b"\xFF\xE0")                                     # call rax

    labels["flush_lp"] = len(m.b)
    m.getproc_call(136, iat_getproc_rva)
    m.jz_short("done")
    m.add(b"\xFF\xE0")                                     # call rax

    labels["done"] = len(m.b)
    m.add(b"\x48\x83\xC4\x28")                             # add rsp, 0x28
    m.add(b"\xC3")                                          # ret
    m.finalize(T_VA, labels)
    return bytes(m.b)


def main():
    # .rdata 固定布局
    off_ux, off_k32, off_ilt, off_impd, off_ename, off_expd = 0x00, 0x10, 0x20, 0x40, 0x60, 0x70
    off_ent, off_ord, off_names, off_load, off_getp = 0xB0, 0xB4, 0xB8, 0xD0, 0xE0

    iat_load_rva = D_VA + 0x00
    iat_getproc_rva = D_VA + 0x08
    ux_rva = R_VA + off_ux

    code = gen_code(iat_load_rva, iat_getproc_rva, ux_rva)
    text_size = (len(code) + 7) & ~7

    ux = b"uxtheme\0"
    k32 = b"kernel32.dll\0"
    ilt = struct.pack("<QQQ", (R_VA + off_load) | 0x80000000,
                      (R_VA + off_getp) | 0x80000000, 0)
    impd = struct.pack("<IIIII", R_VA + off_ilt, 0, 0, R_VA + off_k32, D_VA + 0x00)
    ename = b"EnableDarkMode\0"
    expd = struct.pack("<IIIIIIIIII", 0, 0, 0, R_VA + off_ename, 0, 1, 1,
                       R_VA + off_ent, R_VA + off_names, R_VA + off_ord)
    ent = struct.pack("<I", T_VA)
    ord_t = struct.pack("<I", 0)
    names = struct.pack("<I", R_VA + off_ename)
    load = b"LoadLibraryW\0"
    getp = b"GetProcAddress\0"

    rdata = bytearray(0x100)
    rdata[off_ux:off_ux + len(ux)] = ux
    rdata[off_k32:off_k32 + len(k32)] = k32
    rdata[off_ilt:off_ilt + 24] = ilt
    rdata[off_impd:off_impd + 20] = impd
    rdata[off_ename:off_ename + len(ename)] = ename
    rdata[off_expd:off_expd + 40] = expd
    rdata[off_ent:off_ent + 4] = ent
    rdata[off_ord:off_ord + 4] = ord_t
    rdata[off_names:off_names + 4] = names
    rdata[off_load:off_load + len(load)] = load
    rdata[off_getp:off_getp + len(getp)] = getp
    rdata_size = (0x100 + 15) & ~15

    data = struct.pack("<QQ", 0, 0)          # IAT
    data_size = (0x10 + 15) & ~15

    nsec, optional, coff, pe_off = 3, 240, 20, 0x80
    hdr = bytearray(HDR_RAW)
    hdr[0:2] = b"MZ"
    struct.pack_into("<I", hdr, 0x3C, pe_off)
    p = pe_off
    hdr[p:p + 4] = b"PE\x00\x00"
    p += 4
    struct.pack_into("<H", hdr, p, 0x8664)
    struct.pack_into("<H", hdr, p + 2, nsec)
    struct.pack_into("<I", hdr, p + 16, optional)
    struct.pack_into("<H", hdr, p + 18, 0x0022)
    o = p + 20
    struct.pack_into("<H", hdr, o, 0x020B)
    struct.pack_into("<I", hdr, o + 4, 0x4000)        # SizeOfImage
    struct.pack_into("<I", hdr, o + 8, 0x200)         # SizeOfHeaders
    struct.pack_into("<H", hdr, o + 16, 2)            # Subsystem GUI
    struct.pack_into("<H", hdr, o + 18, 0x0180)       # NX|TSA|DYNAMIC_BASE? 去掉 DYNBASE（无重定位）→ 0x180
    struct.pack_into("<I", hdr, o + 40, 16)
    dd = o + 44
    struct.pack_into("<II", hdr, dd + 0, R_VA + off_expd, 40)
    struct.pack_into("<II", hdr, dd + 8, R_VA + off_impd, 20)
    so = o + optional
    def sec(name, va, vs, raw, rs, ch):
        return struct.pack("<8sIIIIIIHHI", name, vs, va, rs, raw, 0, 0, 0, 0, ch)
    text_raw = align_up(text_size, FA)
    rdata_raw = align_up(rdata_size, FA)
    data_raw = align_up(data_size, FA)
    text_po, rdata_po, data_po = HDR_RAW, HDR_RAW + text_raw, HDR_RAW + text_raw + rdata_raw
    hdr[so:so + 120] = (sec(b".text\x00\x00\x00", T_VA, text_size, text_po, text_raw, 0x60000020)
                        + sec(b".rdata\x00\x00", R_VA, rdata_size, rdata_po, rdata_raw, 0x40000040)
                        + sec(b".data\x00\x00\x00", D_VA, data_size, data_po, data_raw, 0x40000042))

    total = data_po + data_raw
    img = bytearray(total)
    img[0:so + 120] = hdr[0:so + 120]
    img[text_po:text_po + len(code)] = code
    img[rdata_po:rdata_po + len(rdata)] = rdata
    img[data_po:data_po + len(data)] = data
    open(OUT, "wb").write(bytes(img))
    print("darkmode.dll written:", len(img), "bytes; code =", len(code))


if __name__ == "__main__":
    main()
