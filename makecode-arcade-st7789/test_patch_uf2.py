#!/usr/bin/env python3
import struct
import unittest

import patch_uf2 as p


def make_block(addr: int, payload: bytes, family: int = p.UF2_RP2040_FAMILY, n=0, total=1) -> bytes:
    payload = payload + b"\x00" * (p.BLOCK - len(payload))
    blk = bytearray(512)
    struct.pack_into(
        "<IIIIIIII",
        blk,
        0,
        p.UF2_MAGIC_START0,
        p.UF2_MAGIC_START1,
        0x2000,
        addr,
        p.BLOCK,
        n,
        total,
        family,
    )
    blk[32 : 32 + p.BLOCK] = payload[: p.BLOCK]
    struct.pack_into("<I", blk, 508, p.UF2_MAGIC_END)
    return bytes(blk)


class PatchTests(unittest.TestCase):
    def test_st7789_init_fits_slot(self):
        init = p.build_st7789_init(invert=True, madctl=0xA0)
        self.assertEqual(len(init), p.ILI9341_SLOT)
        self.assertEqual(init[0], 0x01)
        self.assertIn(bytes([0x3A, 0x81, 0x55]), init)
        self.assertIn(bytes([0x36, 0x01, 0xA0]), init)
        self.assertIn(bytes([0x21, 0x00]), init)
        off = p.build_st7789_init(invert=False, madctl=0x40)
        self.assertIn(bytes([0x20, 0x00]), off)
        self.assertIn(bytes([0x36, 0x01, 0x40]), off)

    def test_palette_stub_literal(self):
        stub = p.build_palette_stub(0x100FE000)
        self.assertEqual(len(stub), 30)
        self.assertEqual(stub[0x10:0x14], bytes([0x00, 0xE0, 0x0F, 0x10]))

    def test_cf2_magic_and_skip_frmctr(self):
        cf2 = p.build_cf2(p.KUBIT_CF2_ENTRIES, madctl=0xA0, cfg2=0x28)
        self.assertEqual(len(cf2), 4096)
        self.assertEqual(struct.unpack_from("<I", cf2, 0)[0], p.CFG_MAGIC0)
        self.assertEqual(struct.unpack_from("<I", cf2, 4)[0], p.CFG_MAGIC1)
        count = struct.unpack_from("<I", cf2, 8)[0]
        keys = {}
        for i in range(count):
            k, v = struct.unpack_from("<II", cf2, 16 + i * 8)
            keys[k] = v
        self.assertEqual(keys[p.CFG_DISPLAY_TYPE], 9341)
        self.assertEqual(keys[p.CFG_DISPLAY_CFG0], 0xA0)
        self.assertEqual(keys[p.CFG_DISPLAY_CFG1], 0xFFFFFF)
        self.assertEqual(keys[p.CFG_PIN_DISPLAY_CS], 9)
        self.assertEqual(keys[p.CFG_PIN_BTN_A], 26)
        self.assertEqual(keys[p.CFG_PIN_SPEAKER_AMP], 2)
        self.assertEqual(keys[p.CFG_PIN_JACK_SND], 0)
        self.assertEqual(keys[p.CFG_PIN_DISPLAY_BL], 15)
        self.assertNotIn(60, keys)  # JACK_TX must not claim SPEAK_EN

    def test_patch_synthetic_uf2(self):
        firmware = bytearray(0x200)
        firmware[0:7] = p.ILI9341_SIG
        firmware[7:114] = b"\xAA" * (114 - 7)
        firmware[0x80:0x88] = p.ENC16_SIG
        firmware[0x88:0x80 + 30] = b"\x11" * (30 - 8)
        payload0 = bytes(firmware[:256])
        payload1 = bytes(firmware[256:]) + b"\x00" * 56
        uf2 = make_block(0x10000000, payload0, n=0, total=2) + make_block(
            0x10000100, payload1[:256], n=1, total=2
        )
        flash, family = p.parse_uf2(uf2)
        start, img = p.flash_to_image(flash)
        notes = p.patch_image(
            start,
            img,
            madctl=0xA0,
            invert=True,
            spi_mhz=40,
            skip_init=False,
            skip_palette=False,
            skip_cf2=False,
        )
        self.assertIn("patched", notes["ili9341_init"])
        self.assertEqual(bytes(img[0:3]), bytes([0x01, 0x80, 150]))
        self.assertEqual(bytes(img[0x80:0x82]), bytes([0x03, 0x4B]))
        lut_off = 0x100FE000 - start
        self.assertEqual(bytes(img[lut_off : lut_off + 4]), p.ARCADE_PALETTE_LUT[:4])
        cf2_off = 0x100FF000 - start
        self.assertEqual(struct.unpack_from("<I", img, cf2_off)[0], p.CFG_MAGIC0)


    def test_cfg0_without_mv_and_offset(self):
        self.assertEqual(p.pack_cfg0(0x40), 0x40)
        self.assertEqual(p.pack_cfg0(0x40, off_x=80), 0x5040)
        self.assertEqual(p.pack_cfg0(0x40, off_y=80), 0x500040)
        self.assertEqual(0xA0 & 0x20, 0x20)
        self.assertEqual(0x40 & 0x20, 0)


if __name__ == "__main__":
    unittest.main()
