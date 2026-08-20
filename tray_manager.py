"""
Zero-Dependency Windows System Tray Manager for MicroClicker Pro.
Supports 32-bit and 64-bit Windows via ctypes Win32 API bindings.
Provides Left-Click toggle, Right-Click menu, and clean exit.
"""

import sys
import os
import ctypes
import threading
import time

# Win32 Constants
WM_USER = 0x0400
WM_TRAYICON = WM_USER + 20
WM_COMMAND = 0x0111
WM_RBUTTONUP = 0x0205
WM_LBUTTONUP = 0x0202
WM_LBUTTONDBLCLK = 0x0203
WM_DESTROY = 0x0002

NIM_ADD = 0x00000000
NIM_MODIFY = 0x00000001
NIM_DELETE = 0x00000002

NIF_MESSAGE = 0x00000001
NIF_ICON = 0x00000002
NIF_TIP = 0x00000004
NIF_STATE = 0x00000008
NIF_INFO = 0x00000010

IMAGE_ICON = 1
LR_LOADFROMFILE = 0x00000010
LR_DEFAULTSIZE = 0x00000040

TPM_RIGHTBUTTON = 0x0002
TPM_LEFTALIGN = 0x0000
TPM_BOTTOMALIGN = 0x0020
TPM_RETURNCMD = 0x0100

MF_STRING = 0x00000000
MF_SEPARATOR = 0x00000800
MF_CHECKED = 0x00000008
MF_UNCHECKED = 0x00000000

# Menu Command IDs
CMD_TOGGLE = 1001
CMD_SHOW_HIDE = 1002
CMD_SETTINGS = 1003
CMD_EXIT = 1004

if sys.platform == "win32":
    from ctypes import wintypes

    # Handle 64-bit and 32-bit types
    LRESULT = ctypes.c_ssize_t
    WPARAM = wintypes.WPARAM
    LPARAM = wintypes.LPARAM

    class NOTIFYICONDATAW(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("hWnd", wintypes.HWND),
            ("uID", wintypes.UINT),
            ("uFlags", wintypes.UINT),
            ("uCallbackMessage", wintypes.UINT),
            ("hIcon", wintypes.HICON),
            ("szTip", wintypes.WCHAR * 128),
            ("dwState", wintypes.DWORD),
            ("dwStateMask", wintypes.DWORD),
            ("szInfo", wintypes.WCHAR * 256),
            ("uTimeoutOrVersion", wintypes.UINT),
            ("szInfoTitle", wintypes.WCHAR * 64),
            ("dwInfoFlags", wintypes.DWORD),
        ]

    WNDPROC = ctypes.WINFUNCTYPE(
        LRESULT,
        wintypes.HWND,
        wintypes.UINT,
        WPARAM,
        LPARAM
    )

    class WNDCLASSW(ctypes.Structure):
        _fields_ = [
            ("style", wintypes.UINT),
            ("lpfnWndProc", WNDPROC),
            ("cbClsExtra", ctypes.c_int),
            ("cbWndExtra", ctypes.c_int),
            ("hInstance", wintypes.HINSTANCE),
            ("hIcon", wintypes.HICON),
            ("hCursor", wintypes.HICON),
            ("hbrBackground", wintypes.HBRUSH),
            ("lpszMenuName", wintypes.LPCWSTR),
            ("lpszClassName", wintypes.LPCWSTR),
        ]


class SystemTrayManager:
    """
    Manages the Windows Taskbar Notification Area (System Tray) Icon.
    Provides Left-Click Toggle, Right-Click Context Menu, and Clean Exit.
    """

    def __init__(self, clicker, overlay_ui, on_exit_callback=None, icon_path="autoclicker.ico"):
        self.clicker = clicker
        self.overlay_ui = overlay_ui
        self.on_exit_callback = on_exit_callback
        self.icon_path = icon_path if os.path.exists(icon_path) else None

        self._is_win = (sys.platform == "win32")
        self._hwnd = None
        self._nid = None
        self._hicon = None
        self._hmenu = None
        self._thread = None
        self._is_running = False
        self._wndproc_ref = None

    def start(self):
        if not self._is_win:
            return

        self._thread = threading.Thread(target=self._run_tray_thread, daemon=True)
        self._thread.start()

    def _run_tray_thread(self):
        try:
            u32 = ctypes.windll.user32
            k32 = ctypes.windll.kernel32
            s32 = ctypes.windll.shell32

            # Configure explicit types for Win64 / Win32 safety
            u32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
            u32.DefWindowProcW.restype = ctypes.c_ssize_t

            u32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
            u32.RegisterClassW.restype = wintypes.ATOM

            u32.CreateWindowExW.argtypes = [
                wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR,
                wintypes.DWORD, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID
            ]
            u32.CreateWindowExW.restype = wintypes.HWND

            s32.Shell_NotifyIconW.argtypes = [wintypes.DWORD, ctypes.POINTER(NOTIFYICONDATAW)]
            s32.Shell_NotifyIconW.restype = wintypes.BOOL

            # Register Window Class for receiving tray messages
            class_name = f"MicroClickerTrayClass_{int(time.time())}"
            hinstance = k32.GetModuleHandleW(None)

            self._wndproc_ref = WNDPROC(self._window_proc)

            wndclass = WNDCLASSW()
            wndclass.style = 0
            wndclass.lpfnWndProc = self._wndproc_ref
            wndclass.cbClsExtra = 0
            wndclass.cbWndExtra = 0
            wndclass.hInstance = hinstance
            wndclass.hIcon = None
            wndclass.hCursor = None
            wndclass.hbrBackground = None
            wndclass.lpszMenuName = None
            wndclass.lpszClassName = class_name

            atom = u32.RegisterClassW(ctypes.byref(wndclass))
            if not atom:
                return

            self._hwnd = u32.CreateWindowExW(
                0, class_name, "MicroClickerTrayWindow",
                0, 0, 0, 0, 0, None, None, hinstance, None
            )

            if not self._hwnd:
                return

            # Load Icon
            if self.icon_path and os.path.exists(self.icon_path):
                self._hicon = u32.LoadImageW(
                    None, os.path.abspath(self.icon_path),
                    IMAGE_ICON, 16, 16, LR_LOADFROMFILE | LR_DEFAULTSIZE
                )
            if not self._hicon:
                # Load standard application icon
                self._hicon = u32.LoadIconW(None, 32512)  # IDI_APPLICATION

            # Initialize NOTIFYICONDATAW
            self._nid = NOTIFYICONDATAW()
            self._nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
            self._nid.hWnd = self._hwnd
            self._nid.uID = 1
            self._nid.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
            self._nid.uCallbackMessage = WM_TRAYICON
            self._nid.hIcon = self._hicon
            self._nid.szTip = "MicroClicker Pro (Press F6 to Toggle)"

            s32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(self._nid))
            self._is_running = True

            # Standard Win32 Message Loop
            msg = wintypes.MSG()
            while u32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                u32.TranslateMessage(ctypes.byref(msg))
                u32.DispatchMessageW(ctypes.byref(msg))

        except Exception as e:
            print(f"[!] System tray initialization notice: {e}")

    def update_tooltip(self, text):
        if not self._is_win or not self._nid or not self._is_running:
            return
        try:
            self._nid.szTip = text[:127]
            self._nid.uFlags = NIF_TIP
            ctypes.windll.shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(self._nid))
        except Exception:
            pass

    def _show_context_menu(self):
        try:
            u32 = ctypes.windll.user32
            hmenu = u32.CreatePopupMenu()

            status_text = "■ Stop (F6)" if self.clicker.is_running else "▶ Start (F6)"
            u32.AppendMenuW(hmenu, MF_STRING, CMD_TOGGLE, f"MicroClicker: {status_text}")
            u32.AppendMenuW(hmenu, MF_SEPARATOR, 0, "")
            u32.AppendMenuW(hmenu, MF_STRING, CMD_SHOW_HIDE, "Toggle HUD Overlay")
            u32.AppendMenuW(hmenu, MF_STRING, CMD_SETTINGS, "Settings & Profiles...")
            u32.AppendMenuW(hmenu, MF_SEPARATOR, 0, "")
            u32.AppendMenuW(hmenu, MF_STRING, CMD_EXIT, "✕ Exit MicroClicker")

            pt = wintypes.POINT()
            u32.GetCursorPos(ctypes.byref(pt))

            u32.SetForegroundWindow(self._hwnd)
            cmd = u32.TrackPopupMenu(
                hmenu,
                TPM_RETURNCMD | TPM_RIGHTBUTTON | TPM_LEFTALIGN | TPM_BOTTOMALIGN,
                pt.x, pt.y, 0, self._hwnd, None
            )
            u32.DestroyMenu(hmenu)

            if cmd == CMD_TOGGLE:
                act = self.clicker.toggle()
                if self.overlay_ui and hasattr(self.overlay_ui, "root"):
                    self.overlay_ui.root.after(0, lambda: self.overlay_ui.update_badge(act))
                self.update_tooltip(f"MicroClicker: {'ACTIVE (ON)' if act else 'IDLE (OFF)'}")
            elif cmd == CMD_SHOW_HIDE:
                if self.overlay_ui and hasattr(self.overlay_ui, "root"):
                    self.overlay_ui.root.after(0, self._toggle_hud_visibility)
            elif cmd == CMD_SETTINGS:
                if self.overlay_ui and hasattr(self.overlay_ui, "root"):
                    self.overlay_ui.root.after(0, self.overlay_ui.open_settings)
            elif cmd == CMD_EXIT:
                self.stop()
                if self.on_exit_callback:
                    self.on_exit_callback()
                elif self.overlay_ui and hasattr(self.overlay_ui, "root"):
                    self.overlay_ui.root.after(0, self.overlay_ui.root.destroy)
        except Exception as e:
            print(f"[!] Tray menu error: {e}")

    def _toggle_hud_visibility(self):
        if not self.overlay_ui or not hasattr(self.overlay_ui, "root"):
            return
        root = self.overlay_ui.root
        if root.winfo_viewable():
            root.withdraw()
        else:
            root.deiconify()
            root.attributes("-topmost", True)

    def _window_proc(self, hwnd, msg, wparam, lparam):
        if msg == WM_TRAYICON:
            # Under Win64, low-word of lparam contains the mouse event message
            evt = lparam & 0xFFFF
            if evt == WM_RBUTTONUP:
                self._show_context_menu()
            elif evt == WM_LBUTTONUP:
                # Left Click on Tray: Quick Toggle
                act = self.clicker.toggle()
                if self.overlay_ui and hasattr(self.overlay_ui, "root"):
                    self.overlay_ui.root.after(0, lambda: self.overlay_ui.update_badge(act))
                self.update_tooltip(f"MicroClicker: {'ACTIVE (ON)' if act else 'IDLE (OFF)'}")
            elif evt == WM_LBUTTONDBLCLK:
                if self.overlay_ui and hasattr(self.overlay_ui, "root"):
                    self.overlay_ui.root.after(0, self.overlay_ui.open_settings)
            return 0

        elif msg == WM_DESTROY:
            self.stop()
            return 0

        try:
            return ctypes.windll.user32.DefWindowProcW(hwnd, msg, wparam, lparam)
        except Exception:
            return 0

    def stop(self):
        if self._is_win and self._nid and self._is_running:
            self._is_running = False
            try:
                ctypes.windll.shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(self._nid))
            except Exception:
                pass
            if self._hwnd:
                try:
                    ctypes.windll.user32.PostMessageW(self._hwnd, WM_DESTROY, 0, 0)
                except Exception:
                    pass
