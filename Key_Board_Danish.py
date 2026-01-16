import pygame
from evdev import InputDevice, categorize, ecodes
import sys

pygame.init()
WIDTH, HEIGHT = 1680, 960
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Argon ONE UP Keyboard Tester - Danish (dk)")

font_chinese = pygame.font.SysFont("WenQuanYi Zen Hei", 30)

# 输入设备（根据你的系统调整路径，用 ls /dev/input/event* 确认）
device_main = InputDevice('/dev/input/event9')
device_fn   = InputDevice('/dev/input/event13')

# 颜色定义（保持原样）
BACKGROUND      = (40, 44, 52)
PANEL_BG        = (30, 34, 42)
TEXT_COLOR      = (220, 220, 220)
GOOD_COLOR      = (120, 224, 143)
DISABLED_COLOR  = (100, 100, 100)
KEY_COLOR       = (60, 64, 72)
PRESSED_KEY_COLOR = (97, 175, 239)

TEXT_BOX = pygame.Rect(20, 50, WIDTH - 40, 40)

font_large   = pygame.font.SysFont("Arial", 36, bold=True)
font_medium  = pygame.font.SysFont("Arial", 24)
font_small   = pygame.font.SysFont("Arial", 18)

# ==================== 丹麦键盘布局 (dk) - 根据你提供的图片 ====================
keyboard_layout = [
    # F键行（基本相同）
    [{"key": "esc",    "label": "Esc",     "rect": pygame.Rect(20, 100, 70, 40)},
     {"key": "f1",     "label": "F1",      "rect": pygame.Rect(100, 100, 70, 40)},
     {"key": "f2",     "label": "F2",      "rect": pygame.Rect(180, 100, 70, 40)},
     {"key": "f3",     "label": "F3",      "rect": pygame.Rect(260, 100, 70, 40)},
     {"key": "f4",     "label": "F4",      "rect": pygame.Rect(340, 100, 70, 40)},
     {"key": "f5",     "label": "F5",      "rect": pygame.Rect(420, 100, 70, 40)},
     {"key": "f6",     "label": "F6",      "rect": pygame.Rect(500, 100, 70, 40)},
     {"key": "f7",     "label": "F7",      "rect": pygame.Rect(580, 100, 70, 40)},
     {"key": "f8",     "label": "F8",      "rect": pygame.Rect(660, 100, 70, 40)},
     {"key": "f9",     "label": "F9",      "rect": pygame.Rect(740, 100, 70, 40)},
     {"key": "f10",    "label": "F10",     "rect": pygame.Rect(820, 100, 70, 40)},
     {"key": "f11",    "label": "F11",     "rect": pygame.Rect(900, 100, 70, 40)},
     {"key": "f12",    "label": "F12",     "rect": pygame.Rect(980, 100, 70, 40)},
     {"key": "prtscr", "label": "PrtScr",  "rect": pygame.Rect(1060, 100, 70, 40)},
     {"key": "pause",  "label": "Pause",   "rect": pygame.Rect(1140, 100, 70, 40)},
     {"key": "insert", "label": "Insert",  "rect": pygame.Rect(1220, 100, 70, 40)},
     {"key": "delete", "label": "Delete",  "rect": pygame.Rect(1300, 100, 70, 40)}],

    # 数字行 - 丹麦特色：§½ ! " # £ $ % € & / ( ) = ? ` ´ |
    [{"key": "½",   "label": "§ ½",    "rect": pygame.Rect(20, 150, 50, 40)},
     {"key": "1",      "label": "1 !",     "rect": pygame.Rect(80, 150, 50, 40)},
     {"key": "2",      "label": "2 \"",    "rect": pygame.Rect(140, 150, 50, 40)},
     {"key": "3",      "label": "3 #",     "rect": pygame.Rect(200, 150, 50, 40)},
     {"key": "4",      "label": "4 £",     "rect": pygame.Rect(260, 150, 50, 40)},
     {"key": "5",      "label": "5 $",     "rect": pygame.Rect(320, 150, 50, 40)},
     {"key": "6",      "label": "6 %",     "rect": pygame.Rect(380, 150, 50, 40)},
     {"key": "7",      "label": "7 €",     "rect": pygame.Rect(440, 150, 50, 40)},
     {"key": "8",      "label": "8 &",     "rect": pygame.Rect(500, 150, 50, 40)},
     {"key": "9",      "label": "9 /",     "rect": pygame.Rect(560, 150, 50, 40)},
     {"key": "0",      "label": "0 (",     "rect": pygame.Rect(620, 150, 50, 40)},
     {"key": "+",   "label": ") =",     "rect": pygame.Rect(680, 150, 50, 40)},  # 常为 + =
     {"key": "´",  "label": "? ` ´",   "rect": pygame.Rect(740, 150, 50, 40)},  # ´ ` |
     {"key": "backspace","label": "Backspace", "rect": pygame.Rect(800, 150, 100, 40)},
     {"key": "home",   "label": "Home",    "rect": pygame.Rect(960, 150, 50, 40)}],

    # QWERTY 行 - ... P Å ^ ¨ ~
    [{"key": "tab",   "label": "Tab",     "rect": pygame.Rect(20, 240, 70, 40)},
     {"key": "q",     "label": "Q",       "rect": pygame.Rect(100, 240, 50, 40)},
     {"key": "w",     "label": "W",       "rect": pygame.Rect(160, 240, 50, 40)},
     {"key": "e",     "label": "E",       "rect": pygame.Rect(220, 240, 50, 40)},
     {"key": "r",     "label": "R",       "rect": pygame.Rect(280, 240, 50, 40)},
     {"key": "t",     "label": "T",       "rect": pygame.Rect(340, 240, 50, 40)},
     {"key": "y",     "label": "Y",       "rect": pygame.Rect(400, 240, 50, 40)},
     {"key": "u",     "label": "U",       "rect": pygame.Rect(460, 240, 50, 40)},
     {"key": "i",     "label": "I",       "rect": pygame.Rect(520, 240, 50, 40)},
     {"key": "o",     "label": "O",       "rect": pygame.Rect(580, 240, 50, 40)},
     {"key": "p",     "label": "P",       "rect": pygame.Rect(640, 240, 50, 40)},
     {"key": "aa",    "label": "Å å",     "rect": pygame.Rect(700, 240, 50, 40)},  # Å
     {"key": "dead",  "label": "^ ¨ ~",   "rect": pygame.Rect(760, 240, 70, 40)},  # dead key ^ ¨
     {"key": "pgup",  "label": "PgUp",    "rect": pygame.Rect(960, 240, 50, 40)}],

    # ASDF 行 - ... L Æ Ø *
    [{"key": "capslock", "label": "Caps",  "rect": pygame.Rect(20, 290, 90, 40)},
     {"key": "a",     "label": "A",       "rect": pygame.Rect(120, 290, 50, 40)},
     {"key": "s",     "label": "S",       "rect": pygame.Rect(180, 290, 50, 40)},
     {"key": "d",     "label": "D",       "rect": pygame.Rect(240, 290, 50, 40)},
     {"key": "f",     "label": "F",       "rect": pygame.Rect(300, 290, 50, 40)},
     {"key": "g",     "label": "G",       "rect": pygame.Rect(360, 290, 50, 40)},
     {"key": "h",     "label": "H",       "rect": pygame.Rect(420, 290, 50, 40)},
     {"key": "j",     "label": "J",       "rect": pygame.Rect(480, 290, 50, 40)},
     {"key": "k",     "label": "K",       "rect": pygame.Rect(540, 290, 50, 40)},
     {"key": "l",     "label": "L",       "rect": pygame.Rect(600, 290, 50, 40)},
     {"key": "ae",    "label": "Æ æ",     "rect": pygame.Rect(660, 290, 50, 40)},  # Æ
     {"key": "oe",    "label": "Ø ø",     "rect": pygame.Rect(720, 290, 50, 40)},  # Ø
     {"key": "'", "label": "* '",     "rect": pygame.Rect(780, 290, 50, 40)},  # ' *
     {"key": "enter", "label": "Enter",   "rect": pygame.Rect(840, 290, 120, 40)},
     {"key": "pgdn",  "label": "PgDn",    "rect": pygame.Rect(960, 290, 50, 40)}],

    # 底层字母行 - < > Z X ... M , ; : - Ø ? 你的图片有 Ø 在此行？ 但根据图片 Z行是 > Z X C V B N M ; : - Shift
    [{"key": "lshift",    "label": "Shift",   "rect": pygame.Rect(20, 340, 100, 40)},
     {"key": "102nd",     "label": "< > \\",  "rect": pygame.Rect(140, 340, 60, 40)},  # 额外ISO键 < > |
     {"key": "z",         "label": "Z",       "rect": pygame.Rect(210, 340, 50, 40)},
     {"key": "x",         "label": "X",       "rect": pygame.Rect(270, 340, 50, 40)},
     {"key": "c",         "label": "C",       "rect": pygame.Rect(330, 340, 50, 40)},
     {"key": "v",         "label": "V",       "rect": pygame.Rect(390, 340, 50, 40)},
     {"key": "b",         "label": "B",       "rect": pygame.Rect(450, 340, 50, 40)},
     {"key": "n",         "label": "N",       "rect": pygame.Rect(510, 340, 50, 40)},
     {"key": "m",         "label": "M",       "rect": pygame.Rect(570, 340, 50, 40)},
     {"key": "comma",     "label": ", ;",     "rect": pygame.Rect(630, 340, 50, 40)},
     {"key": "period",    "label": ". :",     "rect": pygame.Rect(690, 340, 50, 40)},
     {"key": "minus",     "label": "- _",     "rect": pygame.Rect(750, 340, 50, 40)},
     {"key": "rshift",    "label": "Shift",   "rect": pygame.Rect(810, 340, 140, 40)},
     {"key": "end",       "label": "End",     "rect": pygame.Rect(960, 340, 50, 40)}],

    # 底行 + 方向键（保持类似）
    [{"key": "lctrl", "label": "Ctrl",  "rect": pygame.Rect(20, 390, 70, 40)},
     {"key": "Fn",    "label": "Fn",    "rect": pygame.Rect(100, 390, 70, 40)},
     {"key": "win",   "label": "Win",   "rect": pygame.Rect(180, 390, 70, 40)},
     {"key": "lalt",  "label": "Alt",   "rect": pygame.Rect(260, 390, 70, 40)},
     {"key": "space", "label": "Space", "rect": pygame.Rect(340, 390, 300, 40)},
     {"key": "ralt",  "label": "Alt Gr","rect": pygame.Rect(650, 390, 70, 40)},
     {"key": "compose","label": "Compose","rect": pygame.Rect(730, 390, 70, 40)},
     {"key": "rctrl", "label": "Ctrl",  "rect": pygame.Rect(820, 390, 70, 40)},
     {"key": "left",  "label": "←",     "rect": pygame.Rect(900, 390, 50, 40)},
     {"key": "up",    "label": "↑",     "rect": pygame.Rect(960, 390, 50, 40)},
     {"key": "down",  "label": "↓",     "rect": pygame.Rect(960, 440, 50, 40)},
     {"key": "right", "label": "→",     "rect": pygame.Rect(1020, 390, 50, 40)}]
]

# ==================== evdev 按键映射 - 丹麦布局特殊键 ====================
evdev_key_mapping = {
    # 基于evdev scancode常见映射（调整为丹麦特色键）
    1: "esc",
    2: "1",
    3: "2",
    4: "3",
    5: "4",
    6: "5",
    7: "6",
    8: "7",
    9: "8",
    10: "9",
    11: "0",
    12: "+",     # § ½ (常在 KEY_MINUS 位置)
    13: "´",    # ´ ` (KEY_EQUAL)
    26: "aa",       # Å (KEY_LEFTBRACE, 常用于 [ { 位置)
    27: "dead",     # ^ ¨ (KEY_RIGHTBRACE)
    39: "ae",       # Æ (KEY_SEMICOLON)
    40: "oe",       # Ø (KEY_APOSTROPHE)
    86: "102nd",    # < > | (KEY_102ND, ISO额外键)
    51: "comma",    # , ;
    52: "period",   # . :
    53: "minus",    # - _
    
    43: "'",
    41: "½",
}

standard_keys = {  # 大部分保持原样，通用
    "KEY_ESC": "esc",
    "KEY_1": "1", "KEY_2": "2", "KEY_3": "3", "KEY_4": "4",
    "KEY_5": "5", "KEY_6": "6", "KEY_7": "7", "KEY_8": "8",
    "KEY_9": "9", "KEY_0": "0",
    "KEY_TAB": "tab",
    "KEY_Q": "q", "KEY_W": "w", "KEY_E": "e", "KEY_R": "r",
    "KEY_T": "t", "KEY_Y": "y", "KEY_U": "u", "KEY_I": "i",
    "KEY_O": "o", "KEY_P": "p",
    "KEY_A": "a", "KEY_S": "s", "KEY_D": "d", "KEY_F": "f",
    "KEY_G": "g", "KEY_H": "h", "KEY_J": "j", "KEY_K": "k",
    "KEY_L": "l",
    "KEY_Z": "z", "KEY_X": "x", "KEY_C": "c", "KEY_V": "v",
    "KEY_B": "b", "KEY_N": "n", "KEY_M": "m",
    "KEY_CAPSLOCK": "capslock",
    "KEY_LEFTSHIFT": "lshift", "KEY_RIGHTSHIFT": "rshift",
    "KEY_LEFTCTRL": "lctrl", "KEY_RIGHTCTRL": "rctrl",
    "KEY_LEFTALT": "lalt", "KEY_RIGHTALT": "ralt",
    "KEY_SPACE": "space",
    "KEY_BACKSPACE": "backspace",
    "KEY_ENTER": "enter",
    "KEY_LEFT": "left", "KEY_RIGHT": "right",
    "KEY_UP": "up", "KEY_DOWN": "down",
    "KEY_INSERT": "insert", "KEY_DELETE": "delete",
    "KEY_HOME": "home", "KEY_END": "end",
    "KEY_PAGEUP": "pgup", "KEY_PAGEDOWN": "pgdn",
    "KEY_F1": "f1", "KEY_F2": "f2", "KEY_F3": "f3", "KEY_F4": "f4",
    "KEY_F5": "f5", "KEY_F6": "f6", "KEY_F7": "f7", "KEY_F8": "f8",
    "KEY_F9": "f9", "KEY_F10": "f10", "KEY_F11": "f11", "KEY_F12": "f12",
    "KEY_SYSRQ": "prtscr",
    "KEY_PAUSE": "pause",
    "KEY_LEFTMETA": "win", "KEY_RIGHTMETA": "win",
    "KEY_COMPOSE": "compose",
}

fn_key_mapping = {
    'KEY_BRIGHTNESSUP':   'f3',
    'KEY_BRIGHTNESSDOWN': 'f2',
}

# ==================== 绘图函数（保持原样） ====================
def draw_key(key_data, is_pressed=False, is_highlighted=False):
    color = PRESSED_KEY_COLOR if is_pressed or is_highlighted else KEY_COLOR
    pygame.draw.rect(screen, color, key_data["rect"], border_radius=3)
    pygame.draw.rect(screen, (30, 30, 30), key_data["rect"], 1, border_radius=3)
    label = key_data["label"]
    font = font_small if len(label) > 6 else font_medium
    text_surf = font.render(label, True, TEXT_COLOR)
    text_rect = text_surf.get_rect(center=key_data["rect"].center)
    screen.blit(text_surf, text_rect)

def draw_keyboard(pressed_keys, highlighted_keys, pressed_history):
    screen.fill(BACKGROUND)
    
    title = font_large.render("Argon ONE UP Keyboard Tester - Danish (dk)", True, TEXT_COLOR)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 20))
    
    pygame.draw.rect(screen, PANEL_BG, TEXT_BOX, border_radius=3)
    pygame.draw.rect(screen, (60, 64, 72), TEXT_BOX, 1, border_radius=3)
    
    history_text = ", ".join(pressed_history[-10:])
    hist_surf = font_medium.render(history_text, True, TEXT_COLOR)
    screen.blit(hist_surf, (TEXT_BOX.x + 10, TEXT_BOX.y + 10))
    
    for row in keyboard_layout:
        for key in row:
            draw_key(key, key["key"] in pressed_keys, key["key"] in highlighted_keys)
    
    chinese1 = font_chinese.render("按键测试中...（FN+F2/F3调节亮度，按两次 Fn 键可切换图片模式）", True, DISABLED_COLOR)
    screen.blit(chinese1, (WIDTH // 2 - chinese1.get_width() // 2, HEIGHT - 100))
    
    chinese2 = font_chinese.render("屏幕测试（下一阶段）：屏幕无色差、无亮点等异常后，按 Ctrl+C 退出", True, DISABLED_COLOR)
    screen.blit(chinese2, (WIDTH // 2 - chinese2.get_width() // 2, HEIGHT - 45))
    
    pygame.display.flip()

# ==================== 主测试循环（保持原样） ====================
def keyboard_test_screen():
    pressed_keys = set()
    highlighted_keys = set()
    pressed_history = []
    clock = pygame.time.Clock()
    running = True
    
    all_keys = {k["key"] for row in keyboard_layout for k in row}
    all_keys.add("compose")
    
    while running:
        if highlighted_keys.issuperset(all_keys):
            screen.fill(BACKGROUND)
            for row in keyboard_layout:
                for key in row:
                    pygame.draw.rect(screen, GOOD_COLOR, key["rect"], border_radius=3)
                    pygame.draw.rect(screen, (30, 30, 30), key["rect"], 1, border_radius=3)
                    txt = font_medium.render(key["label"], True, (0, 0, 0))
                    screen.blit(txt, txt.get_rect(center=key["rect"].center))
            msg = font_large.render("ALL KEYS TESTED! EXITING...", True, GOOD_COLOR)
            screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2))
            pygame.display.flip()
            pygame.time.delay(2000)
            break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # 主键盘事件
        try:
            for ev in device_main.read():
                if ev.type == ecodes.EV_KEY:
                    key_event = categorize(ev)
                    keycode_name = key_event.keycode
                    if isinstance(keycode_name, list):
                        keycode_name = keycode_name[0]
                    
                    if key_event.keystate == 1:  # 按下
                        layout_key = evdev_key_mapping.get(key_event.scancode)
                        if not layout_key:
                            layout_key = standard_keys.get(keycode_name)
                        if layout_key:
                            pressed_keys.add(layout_key)
                            highlighted_keys.add(layout_key)
                            pressed_history.append(layout_key.upper() if len(layout_key) == 1 else layout_key)
                    
                    elif key_event.keystate == 0:  # 释放
                        layout_key = evdev_key_mapping.get(key_event.scancode)
                        if not layout_key:
                            layout_key = standard_keys.get(keycode_name)
                        if layout_key and layout_key in pressed_keys:
                            pressed_keys.remove(layout_key)
        except BlockingIOError:
            pass

        # Fn 层（保持原样）
        try:
            for ev in device_fn.read():
                if ev.type == ecodes.EV_KEY:
                    e = categorize(ev)
                    if e.keystate == 1:
                        if e.keycode == 'KEY_FN':
                            pressed_keys.add("Fn")
                            highlighted_keys.add("Fn")
                        elif e.keycode in fn_key_mapping:
                            mapped = fn_key_mapping[e.keycode]
                            pressed_keys.add(mapped)
                            highlighted_keys.add(mapped)
                            highlighted_keys.add("Fn")
                            pressed_history.append(f"Fn+{mapped.upper()}")
        except BlockingIOError:
            pass

        draw_keyboard(pressed_keys, highlighted_keys, pressed_history)
        clock.tick(60)

    device_main.ungrab()
    device_fn.ungrab()

def main():
    try:
        keyboard_test_screen()
    except KeyboardInterrupt:
        print("\n用户按下 Ctrl+C，程序退出")
    finally:
        pygame.quit()
        sys.exit(0)

if __name__ == "__main__":
    main()
