"""
防止多开的简单守卫
只检查是否有同名窗口，有则拉到前台
"""
import sys
import ctypes
from ctypes import windll, wintypes

# Windows API常量
SW_RESTORE = 9
SW_SHOW = 5
GW_HWNDNEXT = 2
GW_HWNDFIRST = 0
GW_HWNDPREV = -2
GW_OWNER = 4
GW_CHILD = 5

USER32 = windll.user32

def find_desktop_pet_window():
    """查找桌宠窗口"""
    def enum_windows_callback(hwnd, lParam):
        if USER32.IsWindowVisible(hwnd):
            length = USER32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buffer = ctypes.create_unicode_buffer(length + 1)
                USER32.GetWindowTextW(hwnd, buffer, length + 1)
                title = buffer.value
                # 检查是否是桌宠窗口
                if 'desktop_pet' in title.lower() or '桌宠' in title:
                    return hwnd
        return 0
    
    # 枚举所有窗口
    hwnd = USER32.GetForegroundWindow()
    while hwnd:
        result = ctypes.c_void_p(enum_windows_callback(hwnd, 0))
        if result.value:
            return result.value
        hwnd = USER32.GetWindow(hwnd, GW_HWNDNEXT)
    return 0

def bring_window_to_front(hwnd):
    """将窗口拉到前台"""
    if hwnd:
        # 恢复窗口（如果是最小化）
        USER32.ShowWindow(hwnd, SW_RESTORE)
        # 激活窗口
        USER32.SetForegroundWindow(hwnd)
        return True
    return False

def check_single_instance():
    """
    检查是否已有实例在运行
    返回True表示可以启动新实例，False表示应激活已有窗口
    """
    hwnd = find_desktop_pet_window()
    if hwnd:
        print(f"检测到已有实例，窗口句柄: {hwnd}")
        bring_window_to_front(hwnd)
        return False
    return True
