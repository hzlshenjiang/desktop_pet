"""测试单实例守卫：验证 on_activate 是否触发"""
import sys
import os
import time
import subprocess
import ctypes

# 清理残留
for lock in ['.desktop_pet.lock', 'dist\\.desktop_pet.lock']:
    if os.path.exists(lock):
        os.remove(lock)

EXE = r'D:\work\Project\desktop_pet\dist\desktop_pet.exe'
MARKER = r'D:\work\Project\desktop_pet\activate_triggered.txt'

# 删除旧标记
if os.path.exists(MARKER):
    os.remove(MARKER)

# 启动第一个实例
proc1 = subprocess.Popen([EXE])
time.sleep(4)
print('=== 第一个实例已启动 ===')

# 找到桌宠窗口
user32 = ctypes.windll.user32
hwnd = user32.FindWindowExW(0, 0, None, "desktop_pet")
print(f'=== 直接FindWindow: {hwnd} ===')

# 启动第二个实例
proc2 = subprocess.Popen([EXE])
time.sleep(4)
rc2 = proc2.poll()
print(f'=== 第二个实例退出码: {rc2} ===')

# 检查 on_activate 是否被触发（通过文件标记）
triggered = os.path.exists(MARKER)
print(f'=== on_activate 被触发: {triggered} ===')

# 如果触发了，读取标记内容
if triggered:
    with open(MARKER, 'r') as f:
        print(f'=== 标记内容: {f.read()} ===')

# 检查窗口状态
fg = user32.GetForegroundWindow()
print(f'=== 前台窗口句柄: {fg} ===')
print(f'=== 桌宠窗口句柄: {hwnd} ===')
print(f'=== 桌宠是否在前台: {fg == hwnd} ===')

# 检查置顶属性
if hwnd:
    GWL_EXSTYLE = -20
    WS_EX_TOPMOST = 0x00000008
    exstyle = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    is_topmost = bool(exstyle & WS_EX_TOPMOST)
    print(f'=== 置顶属性(TOP most): {is_topmost} ===')

proc1.kill()
proc1.wait()
proc2.kill() if proc2.poll() is None else None

# 清理标记
if os.path.exists(MARKER):
    os.remove(MARKER)

print('=== 测试完成 ===')