"""
完全独立的键鼠控制器模块。
不依赖 pynput，直接使用 win32api。
"""
import sys
import os
import ctypes
import threading
import time
from ctypes import wintypes

# Windows constants
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_MOUSEMOVE = 0x0200
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_RBUTTONDOWN = 0x0203
WM_RBUTTONUP = 0x0204
WM_MOUSEWHEEL = 0x020A

# Key codes
VK_TAB = 0x09
VK_SHIFT = 0x10
VK_LSHIFT = 0xA0
VK_RSHIFT = 0xA1
VK_CONTROL = 0x11
VK_LCONTROL = 0xA2
VK_RCONTROL = 0xA3
VK_SPACE = 0x20
VK_Q = 0x51
VK_W = 0x57
VK_E = 0x45
VK_R = 0x52
VK_A = 0x41
VK_S = 0x53
VK_D = 0x44
VK_F = 0x46
VK_Z = 0x5A
VK_X = 0x58
VK_C = 0x43
VK_V = 0x56

class Key:
    """Key codes - compatible with pynput.Key API."""
    space = VK_SPACE
    tab = VK_TAB
    shift = VK_SHIFT
    shift_l = VK_LSHIFT
    shift_r = VK_RSHIFT
    ctrl = VK_CONTROL
    ctrl_l = VK_LCONTROL
    ctrl_r = VK_RCONTROL
    q = VK_Q
    w = VK_W
    e = VK_E
    r = VK_R
    a = VK_A
    s = VK_S
    d = VK_D
    f = VK_F
    z = VK_Z
    x = VK_X
    c = VK_C
    v = VK_V

class Button:
    """Mouse buttons - compatible with pynput.Button API."""
    left = 1
    right = 2
    middle = 3

class KeyCode:
    """Key code wrapper - compatible with pynput.KeyCode API."""
    def __init__(self, vk):
        self.vk = vk
    
    def __repr__(self):
        return f"KeyCode(vk={self.vk})"
    
    def __eq__(self, other):
        if isinstance(other, KeyCode):
            return self.vk == other.vk
        return False

class _Listener:
    """Base listener class."""
    def __init__(self, *args, **kwargs):
        self._running = False
        self._thread = None
    
    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
    
    def stop(self):
        self._running = False
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, *args):
        self.stop()

class KeyboardListener(_Listener):
    """Keyboard listener using low-level keyboard hook."""
    def __init__(self, on_press=None, on_release=None):
        super().__init__()
        self.on_press = on_press
        self.on_release = on_release
        self._hk = None
        self._proc = None
    
    def _run(self):
        # Define hook procedure as a static function
        user32 = ctypes.windll.user32
        
        # Use a simpler approach: poll keyboard state
        while self._running:
            time.sleep(0.01)
            for vk in [VK_Q, VK_W, VK_E, VK_R, VK_A, VK_S, VK_D, VK_F, 
                       VK_Z, VK_X, VK_C, VK_V, VK_TAB, VK_SHIFT, VK_CONTROL, VK_SPACE]:
                is_pressed = ctypes.windll.user32.GetAsyncKeyState(vk) & 0x8000
                if is_pressed:
                    key = KeyCode(vk)
                    if self.on_press:
                        try:
                            self.on_press(key)
                        except:
                            pass

class MouseListener(_Listener):
    """Mouse listener using polling."""
    def __init__(self, on_click=None, on_move=None, on_scroll=None):
        super().__init__()
        self.on_click = on_click
        self.on_move = on_move
        self.on_scroll = on_scroll
        self._last_pos = None
    
    def _run(self):
        while self._running:
            # Get current mouse position
            pos = wintypes.POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(pos))
            x, y = pos.x, pos.y
            
            if (x, y) != self._last_pos:
                if self.on_move:
                    try:
                        self.on_move(x, y)
                    except:
                        pass
                self._last_pos = (x, y)
            
            # Check for mouse clicks
            if ctypes.windll.user32.GetAsyncKeyState(0x01) & 0x8000:  # Left click
                if self.on_click:
                    try:
                        self.on_click(Button.left, x, y)
                    except:
                        pass
            if ctypes.windll.user32.GetAsyncKeyState(0x02) & 0x8000:  # Right click
                if self.on_click:
                    try:
                        self.on_click(Button.right, x, y)
                    except:
                        pass
            
            time.sleep(0.01)

class Controller:
    """Keyboard controller."""
    
    @staticmethod
    def press(key):
        """Press a key."""
        vk = key.vk if isinstance(key, KeyCode) else key
        ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
    
    @staticmethod
    def release(key):
        """Release a key."""
        vk = key.vk if isinstance(key, KeyCode) else key
        ctypes.windll.user32.keybd_event(vk, 0, 2, 0)
    
    @staticmethod
    def click(key):
        """Click a key."""
        Controller.press(key)
        Controller.release(key)

class MouseController:
    """Mouse controller."""
    
    @staticmethod
    def move(x, y):
        """Move mouse to position."""
        ctypes.windll.user32.SetCursorPos(x, y)
    
    @staticmethod
    def click(button=1):
        """Click mouse button."""
        if button == 1:
            ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)
            ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)
        elif button == 2:
            ctypes.windll.user32.mouse_event(0x0008, 0, 0, 0, 0)
            ctypes.windll.user32.mouse_event(0x0010, 0, 0, 0, 0)
    
    @staticmethod
    def scroll(amount):
        """Scroll mouse wheel."""
        ctypes.windll.user32.mouse_event(0x0800, 0, 0, amount * 120, 0)

# Create module-like namespaces
keyboard = type('keyboard', (), {
    'Controller': Controller,
    'Key': Key,
    'KeyCode': KeyCode,
    'Listener': KeyboardListener,
    'press': Controller.press,
    'release': Controller.release,
    'click': Controller.click,
})()

mouse = type('mouse', (), {
    'Controller': MouseController,
    'Button': Button,
    'Listener': MouseListener,
    'move': MouseController.move,
    'click': MouseController.click,
    'scroll': MouseController.scroll,
})()

print('Standalone keyboard/mouse module loaded')
