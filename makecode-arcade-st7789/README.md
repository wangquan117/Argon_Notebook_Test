# MakeCode Arcade：RP2040 + ST7789 偏绿修复

官方 Arcade 固件**没有 ST7789 驱动**。把 `DISPLAY_TYPE` 设成 `ILI9341` 可以出图、按键也能用，但颜色会发绿。这不是引脚配错，**也不是只改 `DISPLAY_CFG0` 就能修好的**。

## 为什么 `0xA0` / `0x010000A8` 都没用

对照 [Adding Arcade hardware — CF2](https://arcade.makecode.com/hardware/adding#cf2)：

| CF2 字段 | 官方含义（ST7735 / ILI9341） | 你这块 ST7789 上实际发生的事 |
| --- | --- | --- |
| `DISPLAY_TYPE = ILI9341` | 走 320×240、像素 2× 放大 | 必须保留，否则只有 160×128 |
| `DISPLAY_CFG0` 低字节 | MADCTL（旋转 / RGB·BGR） | **不要用 `0xA0`（含 MV）**。Arcade 已对调 CASET/RASET，再开 MV 会旋转 90° 并在左边留下约 80px 雪花。默认 `0x40`。 |
| `DISPLAY_CFG0` 的 `0x01000000` | 把调色板 XOR 反相 | 只会正负片式翻转，**去不掉绿罩** |
| `DISPLAY_CFG1` | ILI 的 FRMCTR1（命令 `0xB1`） | ST7789 的 `0xB1` 是 RGBCTRL，应设为 `0xFFFFFF` 跳过 |
| `DISPLAY_CFG2` 低字节 | SPI 时钟（MHz） | 建议 `0x28`（40 MHz），比 50 MHz 稳 |

偏绿来自运行时二进制，不在 CF2：

1. **ILI9341 初始化表**（`0xEF 03 03 80 02 …`）会写 `C0/C5/C7/B1/B6/E0` 等。这些在 ST7789 上是别的寄存器，伽马和底色被拧歪。
2. **CODAL `ST7735.cpp` 的 `double16` 路径**用 `ENC16(i,i,i)` 填灰度查找表，并且**从不改成游戏调色板**，像素就一直发绿/发紫。社区在 [PicoPad Arcade](https://makerclass.cz/picopad-arcade/) 上用同样方法修过。
3. 驱动还会发 **RGBSET `0x2D`**。ILI9341 用它装 LUT；ST7789 的 `0x2D` 不是 LUT。

所以流程应是：**给「游戏 UF2」打补丁**（初始化 + 调色板 + 你的 CF2），再烧录补丁后的文件。不要再覆盖烧录 `arcade-Avoid-the-Fans-2.uf2` 原件。

## 两层改动：CF2 一次，游戏补丁每次

RP2040 上 Arcade 把硬件配置（CF2）放在 Flash 接近末尾（1MB/2MB 前 4KB），游戏程序从 `0x10000000` 起。这是两块互不替代的数据。

| 层 | 写在哪 | 一次烧设备补丁再烧原版游戏，还在吗 | 内容 |
| --- | --- | --- | --- |
| **CF2** | `0x100FF000` / `0x101FF000` | 一般还在（游戏 UF2 通常写不到这里） | 按键、SPI 引脚、`DISPLAY_BL`、`JACK_SND`、`SPEAKER_AMP`、`MADCTL 0x40`、`CFG1=0xFFFFFF` |
| **游戏二进制补丁** | 游戏代码里 | **会被原版游戏盖掉** | ST7789 初始化序列、默认 16 色 LUT（修绿） |

所以：

- **只烧设备 CF2，再烧 MakeCode 原版游戏：按键/音量/亮度/方向配置可以保留，屏幕会再次发绿。**
- 这块是 ST7789，官方运行时仍按 ILI9341 初始化。**每个从 arcade.makecode.com 下载的游戏都要再跑一遍 `patch_uf2.py`。**
- 「先烧补丁、再烧任意原版游戏就全好」只有 ST7735/真 ILI9341 板能成立。ST7789 必须游戏补丁，或做成 PicoPad 那种启动器在烧录时自动打补丁。

生成仅含 CF2 的设备文件（方便恢复引脚，不能单独修绿）：

```powershell
py -3 "D:\downlo\patch_uf2.py" --cf2-only -o "D:\downlo\kubit-factory-cf2.uf2" --madctl 0x40
```

日常换游戏：把 MakeCode 的 `.uf2` **拖到 `PATCH_GAME1.bat` 上**（与 `patch_uf2.py` 放在同一目录，例如 `D:\downlo`）。会在旁边生成 `原名-st7789.uf2`，参数固定为已验证的 `--madctl 0x40`。

```powershell
# 两个文件都放到 D:\downlo 后，把游戏 uf2 拖到 PATCH_GAME1.bat 即可
Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/wangquan117/Argon_Notebook_Test/cursor/st7789-color-fix-2a90/makecode-arcade-st7789/PATCH_GAME1.bat" -OutFile "D:\downlo\PATCH_GAME1.bat"
Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/wangquan117/Argon_Notebook_Test/cursor/st7789-color-fix-2a90/makecode-arcade-st7789/patch_uf2.py" -OutFile "D:\downlo\patch_uf2.py"
```

## 你这块板的引脚（与原理图一致）

RST=GP1，DC=GP8，CS=GP9，SCK=GP10，MOSI=GP11，BL=GP15。RST 有 10 kΩ 下拉，固件里的复位脉冲仍然有效。`LCD_TE`（GP14）Arcade 用不到。

按键：上 22、右 23、下 24、左 25、A 26、B 6（BOOT0）、MENU=21、MENU2=20，都是按下接地，对应 `ACTIVE_LOW_PULL_UP`。

## Windows PowerShell 详细步骤（`D:\downlo`）

`D:\downlo` 里通常**只有游戏 UF2，没有本仓库的 `patch_uf2.py`**。请先下载脚本，再按全路径调用（和 `python "...\patch_arcade_uf2.py" "D:\downlo\....uf2"` 同一写法）：

```powershell
Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/wangquan117/Argon_Notebook_Test/cursor/st7789-color-fix-2a90/makecode-arcade-st7789/patch_uf2.py" -OutFile "D:\downlo\patch_uf2.py"

py -3 "D:\downlo\patch_uf2.py" "D:\downlo\arcade-Avoid-the-Fans-2.uf2" -o "D:\downlo\arcade-Avoid-the-Fans-2-st7789.uf2"
```

必须用原始的 `arcade-Avoid-the-Fans-2.uf2`（约 589312 字节），不要拿已经 `_patched` / `_st7789_init_only` 的文件再打一遍。

你上次这条命令**几乎肯定没有真正跑到脚本**：

```text
PS D:\downlo> python3 makecode-arcade-st7789/patch_uf2.py arcade-Avoid-the-Fans-2.uf2 ...
```

常见两个原因：

1. `D:\downlo` 里没有 `makecode-arcade-st7789\patch_uf2.py`（脚本在本仓库里，不会自动出现在下载目录）。
2. Windows 的 `python3` 经常是「微软商店占位符」，**立刻返回、不报错、不生成文件**。请改用 `py -3` 或 `python`。

### 第 1 步：确认 Python 能用

打开 PowerShell，逐条执行：

```powershell
py -3 --version
python --version
Get-Command python3 | Format-List Source,CommandType
```

- `py -3 --version` 应类似 `Python 3.12.x`。
- 若三条都失败：打开 https://www.python.org/downloads/ 安装，**勾选 Add python.exe to PATH**，关掉并重新打开 PowerShell。
- 若只有 `python3` 能“执行”但 `--version` 弹出商店或什么都不印：不要再用 `python3`。

### 第 2 步：把脚本和游戏固件放到同一文件夹

在 `D:\downlo` 里最终应看到：

```text
D:\downlo\
  arcade-Avoid-the-Fans-2.uf2      ← 你从 arcade.makecode.com 下的原件
  patch_uf2.py                     ← 从本仓库复制
  patch.bat                        ← 可选，双击也能跑
```

复制脚本（任选一种）：

- 浏览器打开并另存为 `D:\downlo\patch_uf2.py`：  
  https://raw.githubusercontent.com/wangquan117/Argon_Notebook_Test/cursor/st7789-color-fix-2a90/makecode-arcade-st7789/patch_uf2.py
- 或从本机仓库复制：

```powershell
Copy-Item -Force .\makecode-arcade-st7789\patch_uf2.py D:\downlo\patch_uf2.py
Copy-Item -Force .\makecode-arcade-st7789\patch.bat D:\downlo\patch.bat
```

检查文件是否真的在：

```powershell
cd D:\downlo
Get-ChildItem patch_uf2.py, arcade-Avoid-the-Fans-2.uf2
```

两个都要列出。缺哪个就补哪个。`arcade-Avoid-the-Fans-2.uf2` 一般有几百 KB～一两 MB；如果只有几十字节，说明下载坏了。

### 第 3 步：打补丁（推荐）

```powershell
cd D:\downlo
py -3 .\patch_uf2.py .\arcade-Avoid-the-Fans-2.uf2
```

成功时会打印类似：

```text
当前目录: D:\downlo
Python: C:\...\python.exe (3.12.x)
读取: D:\downlo\arcade-Avoid-the-Fans-2.uf2 (...... bytes)
已生成: D:\downlo\arcade-Avoid-the-Fans-2-st7789.uf2 (...... bytes)
  ili9341_init: patched 1 site(s) ...
  palette: patched 1 site(s); LUT at 0x100FE000
  cf2: wrote Kubit CF2 ...
```

然后确认新文件：

```powershell
Get-ChildItem D:\downlo\*-st7789.uf2
```

也可以双击 `D:\downlo\patch.bat`（脚本会自己找 `py` / `python`）。

### 第 4 步：烧录

1. 按住板子 **BOOT / BOOTSEL**（原理图上的 BOOT0，你这边接 GP6，也是 B 键），插 USB 或再按复位。
2. 资源管理器出现 `RPI-RP2` 盘。
3. **只拖入** `arcade-Avoid-the-Fans-2-st7789.uf2`。
4. **不要再拖** 原来的 `arcade-Avoid-the-Fans-2.uf2`，否则补丁会被盖掉，又变绿。

### 失败对照

| 现象 | 处理 |
| --- | --- |
| 命令立刻回到 `PS D:\downlo>`，没有任何字 | 不要用 `python3`。改 `py -3`。 |
| `can't open file ... patch_uf2.py` | 脚本不在当前目录，先做第 2 步。 |
| `找不到输入文件` | UF2 文件名不对，用 `dir *.uf2` 看真实名字。 |
| `ILI9341 init signature ... not found` | 不是 Pico/R2 目标下载的 UF2。在 MakeCode 选 **Raspberry Pi Pico (R2)** 再下载。 |
| `ENC16 palette loop signature ... not found` | Arcade 运行时版本变了，把完整报错发回来。 |
| 颜色对、画面转 90°、左边约 1/4 雪花 | `0xA0` 的 MV 位冲突。改用 `--madctl 0x40`（或 `0x80` / `0xC0` / `0x00`，都不要带 `0x20`）。 |
| 生成了 uf2 仍发绿 | 确认烧的是 `*-st7789.uf2`。再试 `--madctl 0x48` 或 `--no-invert`。 |


若方向反了或红蓝反了，改 MADCTL 再打一次补丁（不必改脚本里的引脚）。

**颜色已对、但转 90° 且左边有雪花：** 不要再用 `0xA0` / `0x60` / `0xE0`（这些带 MV=0x20）。Arcade 驱动把 X/Y 写反了，再开 MV 等于转两次，多出来的 80 像素（320−240）就是雪花带。

```powershell
# 先试这个（推荐）
py -3 "D:\downlo\patch_uf2.py" "D:\downlo\arcade-Avoid-the-Fans-2.uf2" -o "D:\downlo\arcade-Avoid-the-Fans-2-st7789.uf2" --madctl 0x40

# 上下或左右反了，在无 MV 的四个值里换：0x00  0x40  0x80  0xC0
# 红蓝反了：给上面的值加 0x08，例如 0x48
# 颜色像负片：加 --no-invert
```

`kubit-st7789.cf2` 可丢进 [UF2 patcher](https://microsoft.github.io/uf2/patcher/) 单独写配置，**只烧 CF2 不够修绿**，必须经过 `patch_uf2.py`。

## 音量和亮度（改 CF2，不用改游戏代码）

这块板没有音量电位器。PAM8302A 是固定增益，音量只能靠 RP2040 改变 PWM 幅度；亮度靠 `LCD_BL` 的 PWM。

| 原理图网络 | GPIO | 正确的 CF2 | 错误做法 |
| --- | --- | --- | --- |
| `LCD_BL` → MOSFET Q2 → `LEDK` | P_15 | `PIN_DISPLAY_BL = P_15`（已有） | 不要拿掉，否则菜单里没有亮度 |
| `SPEAR` → PAM8302 IN+ | P_0 | `PIN_JACK_SND = P_0` | 音频 PWM 必须走这根 |
| `SPEAK_EN` → PAM8302 `SD#` | P_2 | **`PIN_SPEAKER_AMP = P_2`** | **不要**写成 `PIN_JACK_TX`。`SD#` 低有效关断，板上 100k 下拉默认静音 |

把 `PIN_JACK_TX = P_2` 改成 `PIN_SPEAKER_AMP = P_2` 后重新打补丁。Arcade 在音量 > 0 时把 `SPEAK_EN` 拉高打开功放；音量调到 0 再拉低静音。

机内调节：按 **MENU**（原理图 SW7 / GPIO21），系统菜单里有 `VOLUME UP/DOWN` 和 `BRIGHTNESS UP/DOWN`。这是官方菜单，不是游戏积木。

改完后仍用 `--madctl 0x40` 以免方向又乱：

```powershell
Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/wangquan117/Argon_Notebook_Test/cursor/st7789-color-fix-2a90/makecode-arcade-st7789/patch_uf2.py" -OutFile "D:\downlo\patch_uf2.py"

py -3 "D:\downlo\patch_uf2.py" "D:\downlo\arcade-Avoid-the-Fans-2.uf2" -o "D:\downlo\arcade-Avoid-the-Fans-2-st7789.uf2" --madctl 0x40
```

## 补丁做了什么

- 把 114 字节 ILI9341 初始化换成：`SWRESET → SLPOUT → COLMOD=0x55 → MADCTL → INVON → NORON → DISPON`
- 把 ENC16 灰度循环换成从 `0x100FE000` 拷贝 Arcade 默认 16 色 RGB565 表
- 写入本机 CF2：`DISPLAY_TYPE=9341`，`CFG0=0x40`（无 MV），`CFG1=0xFFFFFF`，`CFG2=40`，以及上面的 GPIO

限制：调色板被写死为 Arcade 默认 16 色。用 `setPalette()` 换主题的游戏颜色会不准；Avoid the Fans 这类默认调色板游戏正常。
