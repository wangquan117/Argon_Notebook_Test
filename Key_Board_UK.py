import pygame
import pygame.gfxdraw
import subprocess
import os
import time
import sys
from datetime import datetime
from evdev import InputDevice, categorize, ecodes

pygame.init()

WIDTH, HEIGHT = 1680, 960
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Argon ONE UP Keyboard Tester")


device_main = InputDevice('/dev/input/event9')  
device_fn = InputDevice('/dev/input/event13')   

BACKGROUND = (40, 44, 52)
PANEL_BG = (30, 34, 42)
TEXT_COLOR = (220, 220, 220)
ACCENT_COLOR = (97, 175, 239)
GOOD_COLOR = (120, 224, 143)
WARNING_COLOR = (250, 189, 47)
ERROR_COLOR = (255, 85, 85)
DISABLED_COLOR = (100, 100, 100)
STATUS_BG = (50, 54, 62)
KEY_COLOR = (60, 64, 72)
PRESSED_KEY_COLOR = (97, 175, 239)

TEXT_BOX = pygame.Rect(20, 50, WIDTH - 40, 40)

font_large = pygame.font.SysFont("Arial", 36, bold=True)
font_medium = pygame.font.SysFont("Arial", 24)
font_small = pygame.font.SysFont("Arial", 18)

keyboard_layout = [

    [{"key": "esc", "label": "Esc", "symbol": "", "rect": pygame.Rect(20, 100, 70, 40)},
     {"key": "f1", "label": "F1", "symbol": "", "rect": pygame.Rect(100, 100, 70, 40)},
     {"key": "f2", "label": "F2", "symbol": "", "rect": pygame.Rect(180, 100, 70, 40)},
     {"key": "f3", "label": "F3", "symbol": "", "rect": pygame.Rect(260, 100, 70, 40)},
     {"key": "f4", "label": "F4", "symbol": "", "rect": pygame.Rect(340, 100, 70, 40)},
     {"key": "f5", "label": "F5", "symbol": "", "rect": pygame.Rect(420, 100, 70, 40)},
     {"key": "f6", "label": "F6", "symbol": "", "rect": pygame.Rect(500, 100, 70, 40)},
     {"key": "f7", "label": "F7", "symbol": "", "rect": pygame.Rect(580, 100, 70, 40)},
     {"key": "f8", "label": "F8", "symbol": "", "rect": pygame.Rect(660, 100, 70, 40)},
     {"key": "f9", "label": "F9", "symbol": "", "rect": pygame.Rect(740, 100, 70, 40)},
     {"key": "f10", "label": "F10", "symbol": "", "rect": pygame.Rect(820, 100, 70, 40)},
     {"key": "f11", "label": "F11", "symbol": "", "rect": pygame.Rect(900, 100, 70, 40)},
     {"key": "f12", "label": "F12", "symbol": "", "rect": pygame.Rect(980, 100, 70, 40)},
     {"key": "prtscr", "label": "PrtScr", "symbol": "", "rect": pygame.Rect(1060, 100, 70, 40)},
     {"key": "pause", "label": "Pause", "symbol": "", "rect": pygame.Rect(1140, 100, 70, 40)},
     {"key": "insert", "label": "Insert", "symbol": "", "rect": pygame.Rect(1220, 100, 70, 40)},
     {"key": "delete", "label": "Delete", "symbol": "", "rect": pygame.Rect(1300, 100, 70, 40)}],
    
   
    [{"key": "¬", "label": "¬", "symbol": "", "rect": pygame.Rect(20, 150, 50, 30)},
     {"key": "!", "label": "!", "symbol": "", "rect": pygame.Rect(80, 150, 50, 30)},
     {"key": '"', "label": '"', "symbol": "", "rect": pygame.Rect(140, 150, 50, 30)},
     {"key": "£", "label": "£", "symbol": "", "rect": pygame.Rect(200, 150, 50, 30)},
     {"key": "$", "label": "$", "symbol": "", "rect": pygame.Rect(260, 150, 50, 30)},
     {"key": "%", "label": "%", "symbol": "", "rect": pygame.Rect(320, 150, 50, 30)},
     {"key": "^", "label": "^", "symbol": "", "rect": pygame.Rect(380, 150, 50, 30)},
     {"key": "&", "label": "&", "symbol": "", "rect": pygame.Rect(440, 150, 50, 30)},
     {"key": "*", "label": "*", "symbol": "", "rect": pygame.Rect(500, 150, 50, 30)},
     {"key": "(", "label": "(", "symbol": "", "rect": pygame.Rect(560, 150, 50, 30)},
     {"key": ")", "label": ")", "symbol": "", "rect": pygame.Rect(620, 150, 50, 30)},
     {"key": "_", "label": "_", "symbol": "", "rect": pygame.Rect(680, 150, 50, 30)},
     {"key": "+", "label": "+", "symbol": "", "rect": pygame.Rect(740, 150, 50, 30)},],
    

    [{"key": "`", "label": "`", "symbol": "~", "rect": pygame.Rect(20, 190, 50, 40)},
     {"key": "1", "label": "1", "symbol": "!", "rect": pygame.Rect(80, 190, 50, 40)},
     {"key": "2", "label": "2", "symbol": "@", "rect": pygame.Rect(140, 190, 50, 40)},
     {"key": "3", "label": "3", "symbol": "#", "rect": pygame.Rect(200, 190, 50, 40)},
     {"key": "4", "label": "4", "symbol": "$", "rect": pygame.Rect(260, 190, 50, 40)},
     {"key": "5", "label": "5", "symbol": "%", "rect": pygame.Rect(320, 190, 50, 40)},
     {"key": "6", "label": "6", "symbol": "^", "rect": pygame.Rect(380, 190, 50, 40)},
     {"key": "7", "label": "7", "symbol": "&", "rect": pygame.Rect(440, 190, 50, 40)},
     {"key": "8", "label": "8", "symbol": "*", "rect": pygame.Rect(500, 190, 50, 40)},
     {"key": "9", "label": "9", "symbol": "(", "rect": pygame.Rect(560, 190, 50, 40)},
     {"key": "0", "label": "0", "symbol": ")", "rect": pygame.Rect(620, 190, 50, 40)},
     {"key": "-", "label": "-", "symbol": "_", "rect": pygame.Rect(680, 190, 50, 40)},
     {"key": "=", "label": "=", "symbol": "+", "rect": pygame.Rect(740, 190, 50, 40)},
     {"key": "backspace", "label": "Backspace", "symbol": "", "rect": pygame.Rect(800, 190, 100, 40)},
     {"key": "home", "label": "Home", "symbol": "", "rect": pygame.Rect(960, 190, 50, 40)}],
     

    [{"key": "tab", "label": "Tab", "symbol": "", "rect": pygame.Rect(20, 240, 70, 40)},
     {"key": "q", "label": "Q", "symbol": "", "rect": pygame.Rect(100, 240, 50, 40)},
     {"key": "w", "label": "W", "symbol": "", "rect": pygame.Rect(160, 240, 50, 40)},
     {"key": "e", "label": "E", "symbol": "", "rect": pygame.Rect(220, 240, 50, 40)},
     {"key": "r", "label": "R", "symbol": "", "rect": pygame.Rect(280, 240, 50, 40)},
     {"key": "t", "label": "T", "symbol": "", "rect": pygame.Rect(340, 240, 50, 40)},
     {"key": "y", "label": "Y", "symbol": "", "rect": pygame.Rect(400, 240, 50, 40)},
     {"key": "u", "label": "U", "symbol": "", "rect": pygame.Rect(460, 240, 50, 40)},
     {"key": "i", "label": "I", "symbol": "", "rect": pygame.Rect(520, 240, 50, 40)},
     {"key": "o", "label": "O", "symbol": "", "rect": pygame.Rect(580, 240, 50, 40)},
     {"key": "p", "label": "P", "symbol": "", "rect": pygame.Rect(640, 240, 50, 40)},
     {"key": "[", "label": "[", "symbol": "{", "rect": pygame.Rect(700, 240, 50, 40)},
     {"key": "]", "label": "]", "symbol": "}", "rect": pygame.Rect(760, 240, 50, 40)},
 #    {"key": "\\", "label": "\\", "symbol": "|", "rect": pygame.Rect(820, 240, 70, 40)},
     {"key": "pgup", "label": "PgUp", "symbol": "", "rect": pygame.Rect(960, 240, 50, 40)}],


    [{"key": "caps lock", "label": "Caps", "symbol": "", "rect": pygame.Rect(20, 290, 90, 40)},
     {"key": "a", "label": "A", "symbol": "", "rect": pygame.Rect(120, 290, 50, 40)},
     {"key": "s", "label": "S", "symbol": "", "rect": pygame.Rect(180, 290, 50, 40)},
     {"key": "d", "label": "D", "symbol": "", "rect": pygame.Rect(240, 290, 50, 40)},
     {"key": "f", "label": "F", "symbol": "", "rect": pygame.Rect(300, 290, 50, 40)},
     {"key": "g", "label": "G", "symbol": "", "rect": pygame.Rect(360, 290, 50, 40)},
     {"key": "h", "label": "H", "symbol": "", "rect": pygame.Rect(420, 290, 50, 40)},
     {"key": "j", "label": "J", "symbol": "", "rect": pygame.Rect(480, 290, 50, 40)},
     {"key": "k", "label": "K", "symbol": "", "rect": pygame.Rect(540, 290, 50, 40)},
     {"key": "l", "label": "L", "symbol": "", "rect": pygame.Rect(600, 290, 50, 40)},
     {"key": ";", "label": ";", "symbol": ":", "rect": pygame.Rect(660, 290, 50, 40)},
     {"key": "'", "label": "'", "symbol": "@", "rect": pygame.Rect(720, 290, 50, 40)},
     {"key": "#", "label": "#", "symbol": "~", "rect": pygame.Rect(780, 290, 50, 40)},
     {"key": "enter", "label": "Enter", "symbol": "", "rect": pygame.Rect(840, 290, 120, 40)},
     {"key": "pgdn", "label": "PgDn", "symbol": "", "rect": pygame.Rect(960, 290, 50, 40)}],

   
    [{"key": "lshift", "label": "Shift", "symbol": "", "rect": pygame.Rect(20, 340, 100, 40)},
     {"key": "\\", "label": "\\", "symbol": "|", "rect": pygame.Rect(140, 340, 50, 40)},
     {"key": "z", "label": "Z", "symbol": "", "rect": pygame.Rect(200, 340, 50, 40)},
     {"key": "x", "label": "X", "symbol": "", "rect": pygame.Rect(260, 340, 50, 40)},
     {"key": "c", "label": "C", "symbol": "", "rect": pygame.Rect(320, 340, 50, 40)},
     {"key": "v", "label": "V", "symbol": "", "rect": pygame.Rect(380, 340, 50, 40)},
     {"key": "b", "label": "B", "symbol": "", "rect": pygame.Rect(440, 340, 50, 40)},
     {"key": "n", "label": "N", "symbol": "", "rect": pygame.Rect(500, 340, 50, 40)},
     {"key": "m", "label": "M", "symbol": "", "rect": pygame.Rect(560, 340, 50, 40)},
     {"key": ",", "label": ",", "symbol": "<", "rect": pygame.Rect(620, 340, 50, 40)},
     {"key": ".", "label": ".", "symbol": ">", "rect": pygame.Rect(680, 340, 50, 40)},
     {"key": "/", "label": "/", "symbol": "?", "rect": pygame.Rect(740, 340, 50, 40)},
     {"key": "rshift", "label": "Shift", "symbol": "", "rect": pygame.Rect(800, 340, 150, 40)},
     {"key": "end", "label": "End", "symbol": "", "rect": pygame.Rect(960, 340, 50, 40)}],


    [{"key": "lctrl", "label": "Ctrl", "symbol": "", "rect": pygame.Rect(20, 390, 70, 40)},
     {"key": "Fn", "label": "Fn", "symbol": "", "rect": pygame.Rect(100, 390, 70, 40)},
     {"key": "win", "label": "Win", "symbol": "", "rect": pygame.Rect(180, 390, 70, 40)},
     {"key": "lalt", "label": "Alt", "symbol": "", "rect": pygame.Rect(260, 390, 70, 40)},
     {"key": "space", "label": "Space", "symbol": "", "rect": pygame.Rect(340, 390, 300, 40)},
     {"key": "ralt", "label": "Alt", "symbol": "", "rect": pygame.Rect(650, 390, 70, 40)},
     {"key": "rctrl", "label": "Ctrl", "symbol": "", "rect": pygame.Rect(730, 390, 70, 40)},
     {"key": "left", "label": "left", "symbol": "", "rect": pygame.Rect(820, 390, 50, 40)},
     {"key": "up", "label": "up", "symbol": "", "rect": pygame.Rect(880, 390, 50, 40)},
     {"key": "down", "label": "down", "symbol": "", "rect": pygame.Rect(880, 440, 50, 40)}],


    [{"key": "right", "label": "right", "symbol": "", "rect": pygame.Rect(940, 390, 50, 40)}]
]     
     

special_key_mapping = {
    pygame.K_ESCAPE: "esc",
    pygame.K_F1: "f1",
    pygame.K_F2: "f2",
    pygame.K_F3: "f3",
    pygame.K_F4: "f4",
    pygame.K_F5: "f5",
    pygame.K_F6: "f6",
    pygame.K_F7: "f7",
    pygame.K_F8: "f8",
    pygame.K_F9: "f9",
    pygame.K_F10: "f10",
    pygame.K_F11: "f11",
    pygame.K_F12: "f12",
    pygame.K_PAUSE: "pause",
    pygame.K_SYSREQ: "prtscr",
    pygame.K_INSERT: "insert",
    pygame.K_DELETE: "delete",
    pygame.K_TAB: "tab",
    pygame.K_CAPSLOCK: "caps lock",
    pygame.K_LSHIFT: "lshift",
    pygame.K_RSHIFT: "rshift",
    pygame.K_LCTRL: "lctrl",
    pygame.K_RCTRL: "rctrl",
    pygame.K_LALT: "lalt",
    pygame.K_RALT: "ralt",
    pygame.K_LSUPER: "win",
    pygame.K_RSUPER: "win",
    pygame.K_RETURN: "enter",
    pygame.K_BACKSPACE: "backspace",
    pygame.K_SPACE: "space",
    pygame.K_LEFTBRACKET: "[",
    pygame.K_RIGHTBRACKET: "]",
    92: "\\",  # Backslash
    35: "#",
    pygame.K_SEMICOLON: ";",
    pygame.K_QUOTE: "'",
    pygame.K_COMMA: ",",
    pygame.K_PERIOD: ".",
    pygame.K_SLASH: "/",
    pygame.K_MINUS: "-",
    pygame.K_EQUALS: "=",
    pygame.K_0: "0",
    pygame.K_1: "1",
    pygame.K_2: "2",
    pygame.K_3: "3",
    pygame.K_4: "4",
    pygame.K_5: "5",
    pygame.K_6: "6",
    pygame.K_7: "7",
    pygame.K_8: "8",
    pygame.K_9: "9",
    pygame.K_LEFT: "left",
    pygame.K_RIGHT: "right",
    pygame.K_UP: "up",
    pygame.K_DOWN: "down",
    pygame.K_HOME: "home",
    pygame.K_END: "end",
    pygame.K_PAGEUP: "pgup",
    pygame.K_PAGEDOWN: "pgdn",
 
    #pygame.K_COMPOSE: "compose"
#    127: "compose"
}


shift_special_mapping = {
    pygame.K_BACKQUOTE: "¬",
    pygame.K_0: ")",
    pygame.K_1: "!",
    pygame.K_2: '"',
    pygame.K_3: "£",
    pygame.K_4: "$",
    pygame.K_5: "%",
    pygame.K_6: "^",
    pygame.K_7: "&",
    pygame.K_8: "*",
    pygame.K_9: "(",
    pygame.K_MINUS: "_",
    pygame.K_EQUALS: "+",
    pygame.K_LEFTBRACKET: "{",
    pygame.K_RIGHTBRACKET: "}",
    pygame.K_PERIOD: ">",
    pygame.K_COMMA: "<",
    pygame.K_SLASH: "?",
    pygame.K_SEMICOLON: ":",
    pygame.K_BACKSLASH: "|",
    35: "~",
    pygame.K_QUOTE: '"'
}

fn_key_mapping = {
    'KEY_BRIGHTNESSUP': 'f3',
    'KEY_BRIGHTNESSDOWN': 'f2',
}


def draw_key(key_data, is_pressed=False, caps_lock_on=False, is_highlighted=False):
    color = PRESSED_KEY_COLOR if is_pressed or is_highlighted else KEY_COLOR
    pygame.draw.rect(screen, color, key_data["rect"], border_radius=3)
    pygame.draw.rect(screen, (30, 30, 30), key_data["rect"], 1, border_radius=3)
    
    label = key_data["label"]
    if caps_lock_on and len(label) == 1 and label.isalpha():
        label = label.upper()
    else:
        label = label.lower() if len(label) == 1 and label.isalpha() else label

    font = font_small if len(label) > 1 else font_medium
    text_surf = font.render(label, True, TEXT_COLOR)
    text_rect = text_surf.get_rect(center=key_data["rect"].center)
    screen.blit(text_surf, text_rect)

def draw_keyboard(pressed_keys, highlighted_keys, pressed_history, caps_lock_on):
    screen.fill(BACKGROUND)
    title_surf = font_large.render("Argon ONE UP Keyboard Tester", True, TEXT_COLOR)
    screen.blit(title_surf, (WIDTH//2 - title_surf.get_width()//2, 20))

    pygame.draw.rect(screen, PANEL_BG, TEXT_BOX, border_radius=3)
    pygame.draw.rect(screen, (60, 64, 72), TEXT_BOX, 1, border_radius=3)
    
    history_text = ", ".join(pressed_history[-10:])  
    text_surf = font_medium.render(history_text, True, TEXT_COLOR)
    
    screen.blit(text_surf, (TEXT_BOX.x + 10, TEXT_BOX.y + (TEXT_BOX.height - text_surf.get_height()) // 2))

    for row in keyboard_layout:
        for key in row:
            is_pressed = key["key"] in pressed_keys
            is_highlighted = key["key"] in highlighted_keys
            draw_key(key, is_pressed, caps_lock_on, is_highlighted)

    footer = font_small.render("Press Ctrl+C to exit, Ctrl+Alt+Q to reset highlights", True, DISABLED_COLOR)
    screen.blit(footer, (WIDTH//2 - footer.get_width()//2, HEIGHT - 30))

    pygame.display.flip()
    
    
def keyboard_test_screen():
    pressed_keys = set()
    highlighted_keys = set()  # Track keys that stay highlighted
    pressed_history = []      # Record key press history
    clock = pygame.time.Clock()
    running = True
    shift_pressed = False
    caps_lock_on = False
    ctrl_pressed = False
    alt_pressed = False
    fn_pressed = False  

  
    all_keys = set()
    for row in keyboard_layout:
        for key in row:
            all_keys.add(key["key"])


    all_keys.add("compose")

    while running:

        if highlighted_keys.issuperset(all_keys):
   
            for row in keyboard_layout:
                for key in row:
                    pygame.draw.rect(screen, GOOD_COLOR, key["rect"], border_radius=3)
                    pygame.draw.rect(screen, (30, 30, 30), key["rect"], 1, border_radius=3)
                    text_surf = font_medium.render(key["label"], True, (0, 0, 0))
                    text_rect = text_surf.get_rect(center=key["rect"].center)
                    screen.blit(text_surf, text_rect)
           
            message = font_large.render("ALL KEYS TESTED! EXITING...", True, GOOD_COLOR)
            screen.blit(message, (WIDTH//2 - message.get_width()//2, HEIGHT//2))
            pygame.display.flip()
        
            pygame.time.delay(2000)
            running = False
            break

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_LSHIFT, pygame.K_RSHIFT]:
                    shift_pressed = True
                    key_name = "lshift" if event.key == pygame.K_LSHIFT else "rshift"
                    pressed_keys.add(key_name)
                    highlighted_keys.add(key_name)
                elif event.key in [pygame.K_LCTRL, pygame.K_RCTRL]:
                    ctrl_pressed = True
                    key_name = "lctrl" if event.key == pygame.K_LCTRL else "rctrl"
                    pressed_keys.add(key_name)
                    highlighted_keys.add(key_name)
                elif event.key in [pygame.K_LALT, pygame.K_RALT]:
                    alt_pressed = True
                    key_name = "lalt" if event.key == pygame.K_LALT else "ralt"
                    pressed_keys.add(key_name)
                    highlighted_keys.add(key_name)
                if event.key == pygame.K_c and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    running = False
                elif event.key == pygame.K_q and pygame.key.get_mods() & pygame.KMOD_CTRL and pygame.key.get_mods() & pygame.KMOD_ALT:
                    highlighted_keys.clear()  # Reset all highlights
                elif event.key == pygame.K_CAPSLOCK:
                    caps_lock_on = not caps_lock_on
                    highlighted_keys.add("caps lock")
                    pressed_history.append("caps lock")
                else:
                    mods = pygame.key.get_mods()
                    shift_pressed = bool(mods & pygame.KMOD_SHIFT)
                    ctrl_pressed = bool(mods & pygame.KMOD_CTRL)
                    alt_pressed = bool(mods & pygame.KMOD_ALT)
                    
                    if shift_pressed and event.key in shift_special_mapping:
                        key_name = shift_special_mapping[event.key]
                        display_key_name = key_name
                    elif event.key in special_key_mapping:
                        key_name = special_key_mapping[event.key]
                        display_key_name = key_name
                    else:
                        key_name = pygame.key.name(event.key).lower()  # Normalize to lowercase
                        display_key_name = key_name
                        if len(key_name) == 1 and key_name.isalpha():
                            if caps_lock_on or shift_pressed:
                                display_key_name = display_key_name.upper()
                            else:
                                display_key_name = display_key_name.lower()
                    pressed_keys.add(key_name)
                    highlighted_keys.add(key_name)
                    pressed_history.append(display_key_name)

                    
                    if event.key in [pygame.K_LSHIFT, pygame.K_RSHIFT]:
                        shift_pressed = True
                    if event.key in [pygame.K_LCTRL, pygame.K_RCTRL]:
                        ctrl_pressed = True
                    if event.key in [pygame.K_LALT, pygame.K_RALT]:
                        alt_pressed = True
            elif event.type == pygame.KEYUP:
                if event.key in [pygame.K_LSHIFT, pygame.K_RSHIFT]:
                    shift_pressed = False
                if event.key in [pygame.K_LCTRL, pygame.K_RCTRL]:
                    ctrl_pressed = False
                if event.key in [pygame.K_LALT, pygame.K_RALT]:
                    alt_pressed = False
                
                mods = pygame.key.get_mods()
                shift_pressed = bool(mods & pygame.KMOD_SHIFT)
                
                
                if shift_pressed and event.key in shift_special_mapping:
                    key_name = shift_special_mapping[event.key]
                elif event.key in special_key_mapping:
                    key_name = special_key_mapping[event.key]
                else:
                    key_name = pygame.key.name(event.key).lower()
                    if len(key_name) == 1 and key_name.isalpha():
                        key_name = key_name.lower()

                if key_name in pressed_keys:
                    pressed_keys.remove(key_name)

        # (event9)
        try:
            for ev in device_main.read():
                if ev.type == ecodes.EV_KEY:
                    key_event = categorize(ev)
        
                    if key_event.keycode == 'KEY_LEFTMETA' or key_event.keycode == 'KEY_RIGHTMETA':
                        if key_event.keystate == 1:  
                            pressed_keys.add("win")
                            highlighted_keys.add("win")
                            pressed_history.append("Win")
                        elif key_event.keystate == 0:  
                            if "win" in pressed_keys:
                                pressed_keys.remove("win")
      
                    elif key_event.keycode == 'KEY_COMPOSE':
                        if key_event.keystate == 1: 
                            pressed_keys.add("compose")
                            highlighted_keys.add("compose")
                            pressed_history.append("Compose")
                        elif key_event.keystate == 0:  
                            if "compose" in pressed_keys:
                                pressed_keys.remove("compose")
                                
                    elif key_event.keycode == 'KEY_SYSRQ':
                        if key_event.keystate == 1:
                            pressed_keys.add("prtscr")
                            highlighted_keys.add("prtscr")
                            pressed_history.append("PrtScr")
                        elif key_event.keystate == 0:
                            if "prtscr" in pressed_keys:
                                pressed_keys.remove("prtscr")
                               
        except BlockingIOError:
            pass  


        try:
            for ev in device_fn.read():
                if ev.type == ecodes.EV_KEY:
                    key_event = categorize(ev)
            
                    if key_event.keycode == 'KEY_FN':
                        if key_event.keystate == 1:  
                            fn_pressed = True
                            pressed_keys.add("Fn")
                            highlighted_keys.add("Fn")
                        elif key_event.keystate == 0:  
                            fn_pressed = False
                            if "Fn" in pressed_keys:
                                pressed_keys.remove("Fn")
                    elif key_event.keycode in fn_key_mapping:
                        mapped_key = fn_key_mapping[key_event.keycode]
                        if key_event.keystate == 1:  
                            pressed_keys.add(mapped_key)
                            highlighted_keys.add(mapped_key)
                            highlighted_keys.add("Fn")  
                            pressed_history.append(f"Fn+{mapped_key.upper()}")
                        elif key_event.keystate == 0:  
                            if mapped_key in pressed_keys:
                                pressed_keys.remove(mapped_key)
        except BlockingIOError:
            pass

        draw_keyboard(pressed_keys, highlighted_keys, pressed_history, caps_lock_on)
        clock.tick(30)

 
    device_main.ungrab()
    device_fn.ungrab()
    return                                                                             

def main():
    clock = pygame.time.Clock()
    running = True

    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            keyboard_test_screen()
            running = False
    except KeyboardInterrupt:
        print("Keyboard test interrupted by Ctrl+C, exiting gracefully...", flush=True)
    finally:
        try:
            device_main.ungrab()
            device_fn.ungrab()
        except OSError as e:
            print(f"Warning: Failed to ungrab device: {e}", flush=True)
        print("Keyboard test completed successfully!", flush=True)
        sys.exit(0) 

if __name__ == "__main__":
    main()                    

     
