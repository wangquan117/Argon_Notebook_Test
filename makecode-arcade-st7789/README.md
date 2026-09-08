# MakeCode Arcade：RP2040 + ST7789 偏绿修复

官方 Arcade 固件**没有 ST7789 驱动**。把 `DISPLAY_TYPE` 设成 `ILI9341` 可以出图、按键也能用，但颜色会发绿。这不是引脚配错，**也不是只改 `DISPLAY_CFG0` 就能修好的**。

## 为什么 `0xA0` / `0x010000A8` 都没用

对照 [Adding Arcade hardware — CF2](https://arcade.makecode.com/hardware/adding#cf2)：

| CF2 字段 | 官方含义（ST7735 / ILI9341） | 你这块 ST7789 上实际发生的事 |
| --- | --- | --- |
| `DISPLAY_TYPE = ILI9341` | 走 320×240、像素 2× 放大 | 必须保留，否则只有 160×128 |
| `DISPLAY_CFG0` 低字节 | MADCTL（旋转 / RGB·BGR） | 你用 `0xA0` 方向已经对了 |
| `DISPLAY_CFG0` 的 `0x01000000` | 把调色板 XOR 反相 | 只会正负片式翻转，**去不掉绿罩** |
| `DISPLAY_CFG1` | ILI 的 FRMCTR1（命令 `0xB1`） | ST7789 的 `0xB1` 是 RGBCTRL，应设为 `0xFFFFFF` 跳过 |
| `DISPLAY_CFG2` 低字节 | SPI 时钟（MHz） | 建议 `0x28`（40 MHz），比 50 MHz 稳 |

偏绿来自运行时二进制，不在 CF2：

1. **ILI9341 初始化表**（`0xEF 03 03 80 02 …`）会写 `C0/C5/C7/B1/B6/E0` 等。这些在 ST7789 上是别的寄存器，伽马和底色被拧歪。
2. **CODAL `ST7735.cpp` 的 `double16` 路径**用 `ENC16(i,i,i)` 填灰度查找表，并且**从不改成游戏调色板**，像素就一直发绿/发紫。社区在 [PicoPad Arcade](https://makerclass.cz/picopad-arcade/) 上用同样方法修过。
3. 驱动还会发 **RGBSET `0x2D`**。ILI9341 用它装 LUT；ST7789 的 `0x2D` 不是 LUT。

所以流程应是：**给「游戏 UF2」打补丁**（初始化 + 调色板 + 你的 CF2），再烧录补丁后的文件。不要再覆盖烧录 `arcade-Avoid-the-Fans-2.uf2` 原件。

## 你这块板的引脚（与原理图一致）

RST=GP1，DC=GP8，CS=GP9，SCK=GP10，MOSI=GP11，BL=GP15。RST 有 10 kΩ 下拉，固件里的复位脉冲仍然有效。`LCD_TE`（GP14）Arcade 用不到。

按键：上 22、右 23、下 24、左 25、A 26、B 6（BOOT0）、MENU=21、MENU2=20，都是按下接地，对应 `ACTIVE_LOW_PULL_UP`。

## 用法

需要本机 Python 3（无需第三方库）：

```bash
python3 patch_uf2.py arcade-Avoid-the-Fans-2.uf2 -o arcade-Avoid-the-Fans-2-st7789.uf2
```

然后让 RP2040 进 BOOTSEL，拖入 `*-st7789.uf2`。

若方向反了或红蓝反了，改 MADCTL 再打一次补丁（不必改脚本里的引脚）：

```bash
# 红蓝反了：加上 BGR 位
python3 patch_uf2.py arcade-Avoid-the-Fans-2.uf2 --madctl 0xA8

# 颜色像负片：关掉 INVON
python3 patch_uf2.py arcade-Avoid-the-Fans-2.uf2 --no-invert

# 仍偏色时的其它常用 MADCTL：0x00 0x40 0x60 0x80 0xC0 0xE0
```

`kubit-st7789.cf2` 可丢进 [UF2 patcher](https://microsoft.github.io/uf2/patcher/) 单独写配置，**只烧 CF2 不够修绿**，必须经过 `patch_uf2.py`。

## 补丁做了什么

- 把 114 字节 ILI9341 初始化换成：`SWRESET → SLPOUT → COLMOD=0x55 → MADCTL → INVON → NORON → DISPON`
- 把 ENC16 灰度循环换成从 `0x100FE000` 拷贝 Arcade 默认 16 色 RGB565 表
- 写入本机 CF2：`DISPLAY_TYPE=9341`，`CFG0=0xA0`，`CFG1=0xFFFFFF`，`CFG2=40`，以及上面的 GPIO

限制：调色板被写死为 Arcade 默认 16 色。用 `setPalette()` 换主题的游戏颜色会不准；Avoid the Fans 这类默认调色板游戏正常。
