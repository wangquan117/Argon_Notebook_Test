#!/usr/bin/env python3
"""Patch a MakeCode Arcade RP2040 UF2 so an ST7789 320x240 panel shows correct color.

Official Arcade firmware only knows ST7735 / ILI9341. Using DISPLAY_TYPE=ILI9341
on ST7789 can show a game, but colors look green because:

1. The ILI9341 init table writes ILI-only registers (0xC0/C5/C7/B1/B6/E0...).
   Those opcodes mean different things on ST7789 and distort gamma/color.
2. CODAL ST7735 double16 mode fills expPalette with grayscale ENC16(i,i,i)
   and never updates it from the game palette, so pixels stay green/purple.
3. DISPLAY_CFG1 FRMCTR1 is sent as command 0xB1, which is RGBCTRL on ST7789.

This tool patches the game UF2 (not only CF2):
- Replace the ILI9341 init sequence with a short ST7789 sequence
- Replace the ENC16 grayscale loop with a copy from a hardcoded Arcade palette
- Write CF2 for the Kubit pinout at the RP2040 lookup addresses
"""

from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

UF2_MAGIC_START0 = 0x0A324655
UF2_MAGIC_START1 = 0x9E5D5157
UF2_MAGIC_END = 0x0AB16F30
UF2_RP2040_FAMILY = 0xE48BFF56
FLASH_BASE = 0x10000000
BLOCK = 256

ILI9341_SIG = bytes([0xEF, 0x03, 0x03, 0x80, 0x02, 0xCF, 0x03])
ILI9341_SLOT = 114
ENC16_SIG = bytes([0x4B, 0x01, 0x0B, 0x43, 0xCC, 0x10, 0x04, 0x43])
ENC16_LOOP_LEN = 30
LUT_LEN = 64

# PicoPad-proven ST7789 init in the CODAL sendCmdSeq format:
# cmd, (len | DELAY), [args...], [delay_ms]
# DELAY bit is 0x80. MADCTL here is overwritten later by DISPLAY_CFG0.
ST7789_INIT_PREFIX = bytes(
    [
        0x01, 0x80, 150,  # SWRESET + 150ms
        0x11, 0x80, 255,  # SLPOUT + 255ms
        0x3A, 0x81, 0x55, 10,  # COLMOD = 16bpp + 10ms
        0x36, 0x01, 0x40,  # MADCTL: no MV. CODAL already swaps CASET/RASET.
        0x21, 0x00,  # INVON (typical IPS ST7789)
        0x13, 0x80, 10,  # NORON
        0x29, 0x80, 100,  # DISPON
        0x00, 0x00,  # end
    ]
)

# Arcade default 16-color palette as RGB565 duplicated into uint32 (double16).
ARCADE_PALETTE_LUT = bytes(
    [
        0x00, 0x00, 0x00, 0x00,  # black
        0xFF, 0xFF, 0xFF, 0xFF,  # white
        0xF9, 0x04, 0xF9, 0x04,  # red
        0xFC, 0x98, 0xFC, 0x98,  # pink
        0xFC, 0x06, 0xFC, 0x06,  # orange
        0xFF, 0xA1, 0xFF, 0xA1,  # yellow
        0x24, 0xF4, 0x24, 0xF4,  # teal
        0x7E, 0xEA, 0x7E, 0xEA,  # green
        0x01, 0xF5, 0x01, 0xF5,  # blue
        0x87, 0x9F, 0x87, 0x9F,  # light blue
        0x89, 0x78, 0x89, 0x78,  # purple
        0xA4, 0x13, 0xA4, 0x13,  # light gray
        0x5A, 0x0D, 0x5A, 0x0D,  # dark gray
        0xE6, 0x78, 0xE6, 0x78,  # light pink
        0x92, 0x27, 0x92, 0x27,  # brown
        0x00, 0x00, 0x00, 0x00,  # transparent / black
    ]
)

# configkeys.h
CFG_MAGIC0 = 0x1E9E10F1
CFG_MAGIC1 = 0x20227A79
CFG_PIN_BTN_A = 4
CFG_PIN_BTN_B = 5
CFG_PIN_DISPLAY_SCK = 32
CFG_PIN_DISPLAY_MOSI = 34
CFG_PIN_DISPLAY_CS = 35
CFG_PIN_DISPLAY_DC = 36
CFG_DISPLAY_WIDTH = 37
CFG_DISPLAY_HEIGHT = 38
CFG_DISPLAY_CFG0 = 39
CFG_DISPLAY_CFG1 = 40
CFG_DISPLAY_CFG2 = 41
CFG_PIN_DISPLAY_RST = 43
CFG_PIN_DISPLAY_BL = 44
CFG_PIN_BTN_LEFT = 47
CFG_PIN_BTN_RIGHT = 48
CFG_PIN_BTN_UP = 49
CFG_PIN_BTN_DOWN = 50
CFG_PIN_BTN_MENU = 51
CFG_PIN_JACK_TX = 60
CFG_PIN_JACK_SND = 65
CFG_PIN_BTN_MENU2 = 74
CFG_DISPLAY_TYPE = 78
CFG_DEFAULT_BUTTON_MODE = 202
BUTTON_ACTIVE_LOW_PULL_UP = 0x20  # ACTIVE_LOW | 0x20
DISPLAY_TYPE_ILI9341 = 9341

KUBIT_CF2_ENTRIES = [
    (CFG_PIN_BTN_A, 26),
    (CFG_PIN_BTN_B, 6),
    (CFG_PIN_DISPLAY_SCK, 10),
    (CFG_PIN_DISPLAY_MOSI, 11),
    (CFG_PIN_DISPLAY_CS, 9),
    (CFG_PIN_DISPLAY_DC, 8),
    (CFG_DISPLAY_WIDTH, 320),
    (CFG_DISPLAY_HEIGHT, 240),
    (CFG_DISPLAY_CFG0, 0x40),
    (CFG_DISPLAY_CFG1, 0xFFFFFF),
    (CFG_DISPLAY_CFG2, 0x28),
    (CFG_PIN_DISPLAY_RST, 1),
    (CFG_PIN_DISPLAY_BL, 15),
    (CFG_PIN_BTN_LEFT, 25),
    (CFG_PIN_BTN_RIGHT, 23),
    (CFG_PIN_BTN_UP, 22),
    (CFG_PIN_BTN_DOWN, 24),
    (CFG_PIN_BTN_MENU, 21),
    (CFG_PIN_JACK_TX, 2),
    (CFG_PIN_JACK_SND, 0),
    (CFG_PIN_BTN_MENU2, 20),
    (CFG_DISPLAY_TYPE, DISPLAY_TYPE_ILI9341),
    (CFG_DEFAULT_BUTTON_MODE, BUTTON_ACTIVE_LOW_PULL_UP),
]


def u32(b: bytes, off: int = 0) -> int:
    return struct.unpack_from("<I", b, off)[0]


def pack_u32(v: int) -> bytes:
    return struct.pack("<I", v & 0xFFFFFFFF)


def parse_uf2(data: bytes) -> tuple[dict[int, bytes], int | None]:
    if len(data) % 512 != 0:
        raise ValueError("UF2 size is not a multiple of 512")
    flash: dict[int, bytes] = {}
    family: int | None = None
    for i in range(0, len(data), 512):
        blk = data[i : i + 512]
        if u32(blk, 0) != UF2_MAGIC_START0 or u32(blk, 4) != UF2_MAGIC_START1:
            continue
        if u32(blk, 508) != UF2_MAGIC_END:
            continue
        flags = u32(blk, 8)
        addr = u32(blk, 12)
        payload_size = u32(blk, 16)
        if payload_size != BLOCK:
            continue
        if flags & 0x2000:
            family = u32(blk, 28)
        flash[addr] = blk[32 : 32 + BLOCK]
    if not flash:
        raise ValueError("No UF2 payload blocks found")
    return flash, family


def flash_to_image(flash: dict[int, bytes]) -> tuple[int, bytearray]:
    addrs = sorted(flash)
    start = addrs[0]
    end = addrs[-1] + BLOCK
    img = bytearray(b"\xFF" * (end - start))
    for addr, payload in flash.items():
        off = addr - start
        img[off : off + BLOCK] = payload
    return start, img


def image_to_flash(start: int, img: bytes) -> dict[int, bytes]:
    flash: dict[int, bytes] = {}
    for off in range(0, len(img), BLOCK):
        chunk = bytes(img[off : off + BLOCK])
        if chunk == b"\xFF" * BLOCK:
            continue
        flash[start + off] = chunk
    return flash


def find_all(haystack: bytes, needle: bytes) -> list[int]:
    out: list[int] = []
    start = 0
    while True:
        i = haystack.find(needle, start)
        if i < 0:
            break
        out.append(i)
        start = i + 1
    return out


def build_st7789_init(*, invert: bool, madctl: int) -> bytes:
    seq = bytearray(ST7789_INIT_PREFIX)
    # offsets: MADCTL data at index of 0x36, 0x01, VALUE
    madctl_at = seq.find(bytes([0x36, 0x01]))
    if madctl_at < 0:
        raise RuntimeError("MADCTL missing from init template")
    seq[madctl_at + 2] = madctl & 0xFF
    if not invert:
        inv_at = seq.find(bytes([0x21, 0x00]))
        if inv_at >= 0:
            seq[inv_at] = 0x20  # INVOFF
    out = bytearray(ILI9341_SLOT)
    seq = bytes(seq)
    if len(seq) > ILI9341_SLOT:
        raise RuntimeError("ST7789 init longer than ILI9341 slot")
    out[: len(seq)] = seq
    return bytes(out)


def build_palette_stub(lut_addr: int) -> bytes:
    # Thumb-1 copy of 16 uint32s from lut_addr into r2 (expPalette).
    stub = bytearray(
        [
            0x03, 0x4B,  # ldr r3, [pc, #0x0C]
            0x10, 0x24,  # movs r4, #16
            0x01, 0xCB,  # ldm r3!, {r0}
            0x01, 0xC2,  # stm r2!, {r0}
            0x01, 0x3C,  # subs r4, #1
            0xFB, 0xD1,  # bne loop
            0x07, 0xE0,  # b skip literal
            0x00, 0xBF,  # nop
            0x00, 0x00, 0x00, 0x00,  # literal lut_addr
            0x00, 0xBF, 0x00, 0xBF, 0x00, 0xBF,
            0x00, 0xBF, 0x00, 0xBF,
        ]
    )
    stub[0x10:0x14] = pack_u32(lut_addr)
    if len(stub) != ENC16_LOOP_LEN:
        raise RuntimeError(f"palette stub is {len(stub)} bytes, expected {ENC16_LOOP_LEN}")
    return bytes(stub)


def pack_cfg0(madctl: int, off_x: int = 0, off_y: int = 0) -> int:
    """CFG0: byte0=MADCTL, byte1=offX, byte2=offY.

    Do not set MADCTL MV (0x20). CODAL ST7735::setAddrWindow already writes
    CASET=Y and RASET=X. MV plus that swap yields a 90° image and an 80px
    (320-240) snow band on 240x320 ST7789 panels.
    """
    return (madctl & 0xFF) | ((off_x & 0xFF) << 8) | ((off_y & 0xFF) << 16)


def build_cf2(
    entries: list[tuple[int, int]],
    madctl: int,
    cfg2: int,
    off_x: int = 0,
    off_y: int = 0,
) -> bytes:
    cfg0 = pack_cfg0(madctl, off_x, off_y)
    items = [(k, cfg0 if k == CFG_DISPLAY_CFG0 else v) for k, v in entries]
    items = [(k, cfg2 if k == CFG_DISPLAY_CFG2 else v) for k, v in items]
    buf = bytearray(4096)
    buf[0:4] = pack_u32(CFG_MAGIC0)
    buf[4:8] = pack_u32(CFG_MAGIC1)
    buf[8:12] = pack_u32(len(items))
    buf[12:16] = pack_u32(0x1FA)
    p = 16
    for k, v in items:
        buf[p : p + 4] = pack_u32(k)
        buf[p + 4 : p + 8] = pack_u32(v)
        p += 8
    return bytes(buf)


def write_region(start: int, img: bytearray, addr: int, payload: bytes) -> None:
    if addr < start:
        raise ValueError(f"address 0x{addr:08X} is before image start 0x{start:08X}")
    end_needed = addr + len(payload) - start
    if end_needed > len(img):
        img.extend(b"\xFF" * (end_needed - len(img)))
    off = addr - start
    img[off : off + len(payload)] = payload


def used_end(start: int, img: bytes) -> int:
    last = start
    for off in range(0, len(img), BLOCK):
        if img[off : off + BLOCK] != b"\xFF" * BLOCK:
            last = start + off + BLOCK
    return last


def emit_uf2(flash: dict[int, bytes], family: int | None, fill_to: int | None = None) -> bytes:
    addrs = sorted(flash)
    if fill_to is not None:
        # RP2040-E14: avoid sparse UF2 holes; write 0xFF for empty sectors up to fill_to.
        filled: dict[int, bytes] = {}
        addr = addrs[0]
        while addr < fill_to:
            filled[addr] = flash.get(addr, b"\xFF" * BLOCK)
            addr += BLOCK
        flash = filled
        addrs = sorted(flash)
    out = bytearray()
    total = len(addrs)
    flags = 0x2000 if family is not None else 0
    for n, addr in enumerate(addrs):
        payload = flash[addr]
        if len(payload) != BLOCK:
            payload = payload + b"\x00" * (BLOCK - len(payload))
        blk = bytearray(512)
        struct.pack_into("<IIIIIIII", blk, 0,
                         UF2_MAGIC_START0, UF2_MAGIC_START1, flags, addr,
                         BLOCK, n, total, family or 0)
        blk[32:32 + BLOCK] = payload
        struct.pack_into("<I", blk, 508, UF2_MAGIC_END)
        out += blk
    return bytes(out)


def patch_image(
    start: int,
    img: bytearray,
    *,
    madctl: int,
    invert: bool,
    spi_mhz: int,
    skip_init: bool,
    skip_palette: bool,
    skip_cf2: bool,
    off_x: int = 0,
    off_y: int = 0,
) -> dict[str, str]:
    notes: dict[str, str] = {}
    rel = bytes(img)

    if not skip_init:
        hits = find_all(rel, ILI9341_SIG)
        if not hits:
            raise SystemExit(
                "ILI9341 init signature EF 03 03 80 02 CF 03 not found. "
                "Is this a Raspberry Pi Pico / R2 Arcade UF2?"
            )
        init = build_st7789_init(invert=invert, madctl=madctl)
        for off in hits:
            if off + ILI9341_SLOT > len(img):
                continue
            img[off : off + ILI9341_SLOT] = init
        notes["ili9341_init"] = f"patched {len(hits)} site(s) at " + ", ".join(
            f"0x{start + h:08X}" for h in hits
        )

    lut_addr = 0x100FE000  # 4 KB sector just before the 1 MB CF2 slot
    if not skip_palette:
        hits = find_all(bytes(img), ENC16_SIG)
        if not hits:
            raise SystemExit(
                "ENC16 palette loop signature 4B 01 0B 43 CC 10 04 43 not found. "
                "This runtime build may need an updated signature."
            )
        stub = build_palette_stub(lut_addr)
        for off in hits:
            img[off : off + ENC16_LOOP_LEN] = stub
        lut_sector = ARCADE_PALETTE_LUT + b"\xFF" * (4096 - LUT_LEN)
        write_region(start, img, lut_addr, lut_sector)
        notes["palette"] = f"patched {len(hits)} site(s); LUT at 0x{lut_addr:08X}"

    if not skip_cf2:
        cf2 = build_cf2(
            KUBIT_CF2_ENTRIES,
            madctl=madctl,
            cfg2=spi_mhz & 0xFF,
            off_x=off_x,
            off_y=off_y,
        )
        # Arcade looks 4 KB before the end of 1 MB and 2 MB (typical RP2040 sizes).
        for mb in (1, 2):
            addr = FLASH_BASE + mb * 1024 * 1024 - 4096
            write_region(start, img, addr, cf2)
        notes["cf2"] = "wrote Kubit CF2 at 0x100FF000 and 0x101FF000"

    notes["used_end"] = f"0x{used_end(start, img):08X}"
    return notes


def _configure_stdio() -> None:
    if sys.platform != "win32":
        return
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass


def _pick_input_uf2() -> Path | None:
    here = Path.cwd()
    hits = [
        f
        for f in here.glob("*.uf2")
        if "-st7789" not in f.stem.lower() and f.is_file()
    ]
    if len(hits) == 1:
        return hits[0]
    return None


def main(argv: list[str] | None = None) -> int:
    _configure_stdio()
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "uf2",
        nargs="?",
        type=Path,
        help="Arcade game UF2 from arcade.makecode.com (R2 / Pico). "
        "If omitted, uses the only *.uf2 in the current folder.",
    )
    p.add_argument("-o", "--output", type=Path, help="Output UF2 (default: <name>-st7789.uf2)")
    p.add_argument(
        "--madctl",
        default="0x40",
        help="DISPLAY_CFG0 MADCTL. Default 0x40 (no MV). "
        "0xA0 includes MV and rotates 90° with an 80px snow band on this driver.",
    )
    p.add_argument("--off-x", type=int, default=0, help="DISPLAY_CFG0 X offset (0-255)")
    p.add_argument("--off-y", type=int, default=0, help="DISPLAY_CFG0 Y offset (0-255)")
    p.add_argument("--spi-mhz", type=int, default=40, help="SPI frequency in MHz (CFG2 low byte)")
    p.add_argument("--no-invert", action="store_true", help="Send INVOFF instead of INVON")
    p.add_argument("--skip-init", action="store_true")
    p.add_argument("--skip-palette", action="store_true")
    p.add_argument("--skip-cf2", action="store_true")
    p.add_argument(
        "--e14-pad",
        action="store_true",
        help="Fill 0xFF gaps up to 2MB (RP2040-E14 workaround; much larger UF2)",
    )
    args = p.parse_args(argv)

    print(f"当前目录: {Path.cwd()}")
    print(f"Python: {sys.executable} ({sys.version.split()[0]})")

    uf2_path = args.uf2
    if uf2_path is None:
        uf2_path = _pick_input_uf2()
        if uf2_path is None:
            p.error(
                "没有指定 UF2，当前目录也找不到唯一的游戏固件。\n"
                "请把 patch_uf2.py 和 arcade-Avoid-the-Fans-2.uf2 放在同一文件夹后重试，例如:\n"
                "  py -3 patch_uf2.py arcade-Avoid-the-Fans-2.uf2"
            )
        print(f"未指定输入文件，自动使用: {uf2_path.name}")

    uf2_path = uf2_path.expanduser()
    if not uf2_path.is_file():
        raise SystemExit(
            f"找不到输入文件: {uf2_path.resolve() if uf2_path.exists() else uf2_path}\n"
            f"当前目录内容请用 dir *.uf2 检查。Windows 上请用 py -3 而不是 python3。"
        )

    madctl = int(args.madctl, 0) & 0xFF
    print(f"读取: {uf2_path.resolve()} ({uf2_path.stat().st_size} bytes)")
    print(f"MADCTL=0x{madctl:02X} off=({args.off_x},{args.off_y})")
    data = uf2_path.read_bytes()
    flash, family = parse_uf2(data)
    if family not in (None, UF2_RP2040_FAMILY):
        print(f"warning: UF2 family 0x{family:08X} is not RP2040", file=sys.stderr)
    start, img = flash_to_image(flash)
    notes = patch_image(
        start,
        img,
        madctl=madctl,
        invert=not args.no_invert,
        spi_mhz=args.spi_mhz,
        skip_init=args.skip_init,
        skip_palette=args.skip_palette,
        skip_cf2=args.skip_cf2,
        off_x=args.off_x,
        off_y=args.off_y,
    )
    new_flash = image_to_flash(start, img)
    fill_to = FLASH_BASE + 2 * 1024 * 1024 if args.e14_pad else None
    out = emit_uf2(new_flash, family or UF2_RP2040_FAMILY, fill_to=fill_to)
    dest = args.output or uf2_path.with_name(uf2_path.stem + "-st7789.uf2")
    dest = dest.expanduser()
    dest.write_bytes(out)
    print(f"已生成: {dest.resolve()} ({len(out)} bytes)")
    for k, v in notes.items():
        print(f"  {k}: {v}")
    print("请用 BOOTSEL 模式烧录这个新文件，不要再覆盖烧录原来的 arcade-*.uf2。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
