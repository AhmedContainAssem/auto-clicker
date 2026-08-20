"""
Ultra-low-overhead DirectInput & Win32 SendInput controller.
Optimized for MINIMAL hardware resource consumption:
- Pre-allocated ctypes C structs (0 heap allocations during click loops, 0 GC churn)
- High-precision multimedia timer (timeBeginPeriod) for 0.0% CPU sleep states
- Low-level hardware scancodes that bypass DirectX, RawInput, and game filters
"""

import ctypes
import time
from ctypes import wintypes

# Win32 Constants
INPUT_MOUSE = 0
INPUT_KEYBOARD = 1

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_XDOWN = 0x0080
MOUSEEVENTF_XUP = 0x0100

XBUTTON1 = 0x0001
XBUTTON2 = 0x0002

# DirectInput Hardware Scancode Lookup (O(1) memory-efficient dict)
SCANCODES = {
    'escape': 0x01, '1': 0x02, '2': 0x03, '3': 0x04, '4': 0x05, '5': 0x06,
    '6': 0x07, '7': 0x08, '8': 0x09, '9': 0x0A, '0': 0x0B, '-': 0x0C, '=': 0x0D,
    'backspace': 0x0E, 'tab': 0x0F, 'q': 0x10, 'w': 0x11, 'e': 0x12, 'r': 0x13,
    't': 0x14, 'y': 0x15, 'u': 0x16, 'i': 0x17, 'o': 0x18, 'p': 0x19, '[': 0x1A,
    ']': 0x1B, 'enter': 0x1C, 'ctrl': 0x1D, 'ctrl_l': 0x1D, 'a': 0x1E, 's': 0x1F,
    'd': 0x20, 'f': 0x21, 'g': 0x22, 'h': 0x23, 'j': 0x24, 'k': 0x25, 'l': 0x26,
    ';': 0x27, "'": 0x28, '`': 0x29, 'shift': 0x2A, 'shift_l': 0x2A, '\\': 0x2B,
    'z': 0x2C, 'x': 0x2D, 'c': 0x2E, 'v': 0x2F, 'b': 0x30, 'n': 0x31, 'm': 0x32,
    ',': 0x33, '.': 0x34, '/': 0x35, 'shift_r': 0x36, 'alt': 0x38, 'space': 0x39,
    'caps_lock': 0x3A, 'f1': 0x3B, 'f2': 0x3C, 'f3': 0x3D, 'f4': 0x3E, 'f5': 0x3F,
    'f6': 0x40, 'f7': 0x41, 'f8': 0x42, 'f9': 0x43, 'f10': 0x44, 'num_lock': 0x45,
    'scroll_lock': 0x46, 'f11': 0x57, 'f12': 0x58, 'up': 0x48, 'down': 0x50,
    'left': 0x4B, 'right': 0x4D, 'insert': 0x52, 'delete': 0x53, 'home': 0x47,
    'end': 0x4F, 'page_up': 0x49, 'page_down': 0x51
}

EXTENDED_KEYS = {'up', 'down', 'left', 'right', 'insert', 'delete', 'home', 'end', 'page_up', 'page_down', 'ctrl_r', 'alt_r'}

# CTypes Structures
class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG))
    ]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG))
    ]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD)
    ]

class _INPUTunion(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT)
    ]

class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("union", _INPUTunion)
    ]


class UltraLightHardwareInput:
    """
    Zero-heap-allocation Win32 SendInput controller.
    Reuses pre-allocated C structures to ensure zero memory allocations per click.
    """

    def __init__(self):
        self._is_win = hasattr(ctypes, "windll")
        if self._is_win:
            self._user32 = ctypes.windll.user32
            # Enable 1ms timer resolution for OS sleep (prevents busy-wait CPU burn)
            try:
                ctypes.windll.winmm.timeBeginPeriod(1)
            except Exception:
                pass
        else:
            self._user32 = None

        # Pre-allocated reusable structures
        self._extra = ctypes.c_ulong(0)
        self._extra_ptr = ctypes.pointer(self._extra)

        # Pre-allocated single input struct & pointer
        self._inp = INPUT()
        self._inp_ptr = ctypes.pointer(self._inp)
        self._sizeof_inp = ctypes.sizeof(INPUT)

    def __del__(self):
        if hasattr(ctypes, "windll"):
            try:
                ctypes.windll.winmm.timeEndPeriod(1)
            except Exception:
                pass

    def _get_scancode(self, key_name: str) -> int:
        k = key_name.lower().strip()
        if k in SCANCODES:
            return SCANCODES[k]
        if self._is_win and len(k) == 1:
            try:
                vk = self._user32.VkKeyScanW(ord(k[0])) & 0xFF
                sc = self._user32.MapVirtualKeyW(vk, 0)
                if sc:
                    return sc
            except Exception:
                pass
        return 0x21  # Default to 'F'

    def key_down(self, key_name: str):
        sc = self._get_scancode(key_name)
        flags = KEYEVENTF_SCANCODE
        if key_name.lower() in EXTENDED_KEYS:
            flags |= KEYEVENTF_EXTENDEDKEY

        self._inp.type = INPUT_KEYBOARD
        self._inp.union.ki.wVk = 0
        self._inp.union.ki.wScan = sc
        self._inp.union.ki.dwFlags = flags
        self._inp.union.ki.time = 0
        self._inp.union.ki.dwExtraInfo = self._extra_ptr
        if self._is_win and self._user32:
            self._user32.SendInput(1, self._inp_ptr, self._sizeof_inp)

    def key_up(self, key_name: str):
        sc = self._get_scancode(key_name)
        flags = KEYEVENTF_SCANCODE | KEYEVENTF_KEYUP
        if key_name.lower() in EXTENDED_KEYS:
            flags |= KEYEVENTF_EXTENDEDKEY

        self._inp.type = INPUT_KEYBOARD
        self._inp.union.ki.wVk = 0
        self._inp.union.ki.wScan = sc
        self._inp.union.ki.dwFlags = flags
        self._inp.union.ki.time = 0
        self._inp.union.ki.dwExtraInfo = self._extra_ptr
        if self._is_win and self._user32:
            self._user32.SendInput(1, self._inp_ptr, self._sizeof_inp)

    def mouse_down(self, button_name: str):
        btn = button_name.lower().strip()
        flags = MOUSEEVENTF_LEFTDOWN
        data = 0

        if btn in ('right', 'mouse2', 'rclick'):
            flags = MOUSEEVENTF_RIGHTDOWN
        elif btn in ('middle', 'mouse3', 'mclick'):
            flags = MOUSEEVENTF_MIDDLEDOWN
        elif btn in ('mouse4', 'xbutton1'):
            flags = MOUSEEVENTF_XDOWN
            data = XBUTTON1
        elif btn in ('mouse5', 'xbutton2'):
            flags = MOUSEEVENTF_XDOWN
            data = XBUTTON2

        self._inp.type = INPUT_MOUSE
        self._inp.union.mi.dx = 0
        self._inp.union.mi.dy = 0
        self._inp.union.mi.mouseData = data
        self._inp.union.mi.dwFlags = flags
        self._inp.union.mi.time = 0
        self._inp.union.mi.dwExtraInfo = self._extra_ptr
        if self._is_win and self._user32:
            self._user32.SendInput(1, self._inp_ptr, self._sizeof_inp)

    def mouse_up(self, button_name: str):
        btn = button_name.lower().strip()
        flags = MOUSEEVENTF_LEFTUP
        data = 0

        if btn in ('right', 'mouse2', 'rclick'):
            flags = MOUSEEVENTF_RIGHTUP
        elif btn in ('middle', 'mouse3', 'mclick'):
            flags = MOUSEEVENTF_MIDDLEUP
        elif btn in ('mouse4', 'xbutton1'):
            flags = MOUSEEVENTF_XUP
            data = XBUTTON1
        elif btn in ('mouse5', 'xbutton2'):
            flags = MOUSEEVENTF_XUP
            data = XBUTTON2

        self._inp.type = INPUT_MOUSE
        self._inp.union.mi.dx = 0
        self._inp.union.mi.dy = 0
        self._inp.union.mi.mouseData = data
        self._inp.union.mi.dwFlags = flags
        self._inp.union.mi.time = 0
        self._inp.union.mi.dwExtraInfo = self._extra_ptr
        if self._is_win and self._user32:
            self._user32.SendInput(1, self._inp_ptr, self._sizeof_inp)

    def trigger_press(self, target: str, is_mouse: bool, dwell_time: float = 0.020):
        """Dispatches press and release with hardware dwell time without allocating memory."""
        if is_mouse:
            self.mouse_down(target)
            if dwell_time > 0:
                time.sleep(dwell_time)
            self.mouse_up(target)
        else:
            self.key_down(target)
            if dwell_time > 0:
                time.sleep(dwell_time)
            self.key_up(target)
