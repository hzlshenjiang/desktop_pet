import sys
import os
import random
import math
import time

# Patch pynput for PyInstaller compatibility BEFORE any import
# pynput uses relative imports which fail in frozen environment
_patched = False
try:
    if 'pynput._util' not in sys.modules:
        import pynput._util as _pynput_util
        _orig_backend = _pynput_util.backend
        def _patched_backend(package):
            import importlib
            import os as _os
            import sys as _sys
            backend_name = _os.environ.get(
                'PYNPUT_BACKEND_{}'.format(package.rsplit('.')[-1].upper()),
                _os.environ.get('PYNPUT_BACKEND', None),
            )
            if backend_name:
                modules = [backend_name]
            elif _sys.platform == 'darwin':
                modules = ['darwin']
            elif _sys.platform == 'win32':
                modules = ['win32']
            else:
                modules = ['xorg']
            for module in modules:
                try:
                    return importlib.import_module(package + '._' + module)
                except ImportError:
                    pass
            return _orig_backend(package)
        _pynput_util.backend = _patched_backend
        _patched = True
        print('Patched pynput.backend for PyInstaller compatibility')
except Exception as _e:
    print(f'Warning: pynput patch failed: {_e}')
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QMenu, QAction,
                             QVBoxLayout, QSystemTrayIcon)
from PyQt5.QtGui import (QPixmap, QPainter, QColor, QFont, QPolygon, QIcon,
                         QRadialGradient, QBrush, QPen)
from PyQt5.QtCore import Qt, QTimer, QPoint, QPropertyAnimation, QEasingCurve, QRect, QSize

# 全局键鼠监听
import pynput_patch  # noqa: F401
from pynput_patch import keyboard, mouse

# 单实例守卫
from single_instance_guard import SingleInstanceGuard

# 全局守卫引用，防止被释放
_single_guard = None


def bring_to_front(widget):
    """参考QZCAD MainWindow::bringToFront实现，把窗口拉到前台"""
    # 1. 恢复最小化 / 显示隐藏窗口
    if widget.isMinimized():
        widget.showNormal()
    elif not widget.isVisible():
        widget.show()

    # 2. Qt 标准方式
    widget.raise_()
    widget.activateWindow()

    # 3. win32 API 强制置顶激活
    try:
        import ctypes
        hwnd = int(widget.winId())
        user32 = ctypes.windll.user32

        # 先临时置顶（HWND_TOPMOST）再拉到前台，最后恢复（HWND_NOTOPMOST）
        user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0002 | 0x0001 | 0x0040)  # HWND_TOPMOST
        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)
        user32.SetActiveWindow(hwnd)
        user32.SwitchToThisWindow(hwnd, True)
        # 恢复非置顶（临时置顶一次，不修改置顶设置）
        user32.SetWindowPos(hwnd, -2, 0, 0, 0, 0, 0x0002 | 0x0001 | 0x0040)  # HWND_NOTOPMOST
    except Exception:
        pass


def resource_path(relative_path):
    """获取资源文件路径（兼容PyInstaller打包）"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def get_autostart_path():
    """获取开机自启动快捷方式路径"""
    import winreg
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders")
        startup_dir, _ = winreg.QueryValueEx(key, "Startup")
        winreg.CloseKey(key)
    except Exception:
        startup_dir = os.path.join(os.environ.get("APPDATA", ""),
                                   r"Microsoft\Windows\Start Menu\Programs\Startup")
    return os.path.join(startup_dir, "desktop_pet.lnk")


def is_autostart_enabled():
    return os.path.exists(get_autostart_path())


def set_autostart(enable):
    lnk_path = get_autostart_path()
    if enable:
        if os.path.exists(lnk_path):
            return True
        try:
            import pythoncom
            from win32com.shell import shell
            shortcut = pythoncom.CoCreateInstance(
                shell.CLSID_ShellLink, None,
                pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink)
            if getattr(sys, 'frozen', False):
                shortcut.SetPath(sys.executable)
                shortcut.SetWorkingDirectory(os.path.dirname(sys.executable))
            else:
                shortcut.SetPath(sys.executable)
                shortcut.SetArguments(os.path.abspath("desktop_pet.py"))
                shortcut.SetWorkingDirectory(os.path.abspath("."))
            shortcut.SetIconLocation(resource_path("icon.ico"), 0)
            persist = shortcut.QueryInterface(pythoncom.IID_IPersistFile)
            persist.Save(lnk_path, 0)
            return True
        except ImportError:
            try:
                exe_path = sys.executable if getattr(sys, 'frozen', False) else f'"{sys.executable}" "{os.path.abspath("desktop_pet.py")}"'
                bat_content = f'@echo off\nstart "" {exe_path}\n'
                bat_path = os.path.join(os.path.dirname(lnk_path), "desktop_pet.bat")
                with open(bat_path, 'w', encoding='gbk') as f:
                    f.write(bat_content)
                return True
            except Exception:
                return False
    else:
        try:
            if os.path.exists(lnk_path):
                os.remove(lnk_path)
            bat_path = lnk_path.replace(".lnk", ".bat")
            if os.path.exists(bat_path):
                os.remove(bat_path)
            return True
        except Exception:
            return False


# 对话语录
DIALOGUES = [
    "你好呀~",
    "在忙什么呢？",
    "摸摸头~",
    "一起加油吧！",
    "好累呀...",
    "想吃好吃的！",
    "嘿嘿嘿",
    "别看我啦",
    "工作辛苦了",
    "陪我玩一会儿嘛~",
    "你点我啦！",
    "跳高高！",
    "晕乎乎~",
    "被压扁啦！",
    "今天也要元气满满哦！",
    "有什么我能帮忙的吗？",
    "嘻嘻~",
    "发呆中...",
    "稻妻神里流太刀术皆传——神里绫华，参上！请多指教哦",
    "像这样悠闲安稳的时光，如果再多一点就好了…我真贪心啊",
    "雪霁银妆素，桔高映琼枝。嗯…美景当前，只差一壶茶与之相衬呢",
    "剑，就和茶一样，细细品味才能理解其中风雅",
    "樱吹雪",
    "神里流…霜灭",
    "王手~",
]


# ========== 键盘按键配置（相对坐标，0~1） ==========
# 格式: {键名: (cx, cy, rx, ry, type)}
# type: 'circle' 圆形, 'rect' 圆角矩形
KEY_CONFIG = {
    # 紫色圆形按键 - 第三排（最上面一排）
    'z':     (0.275, 0.795, 0.030, 0.030, 'circle'),
    'x':     (0.355, 0.795, 0.030, 0.030, 'circle'),
    'c':     (0.435, 0.795, 0.030, 0.030, 'circle'),
    'v':     (0.515, 0.795, 0.030, 0.030, 'circle'),
    # 紫色圆形按键 - 第二排
    'a':     (0.235, 0.850, 0.030, 0.030, 'circle'),
    's':     (0.395, 0.850, 0.030, 0.030, 'circle'),
    'd':     (0.475, 0.850, 0.030, 0.030, 'circle'),
    'f':     (0.555, 0.850, 0.030, 0.030, 'circle'),
    # 青绿色空格/回车
    'space': (0.315, 0.850, 0.032, 0.032, 'circle'),
    # 紫色圆形按键 - 第一排（最下面一排）
    'q':     (0.195, 0.910, 0.030, 0.030, 'circle'),
    'w':     (0.275, 0.910, 0.030, 0.030, 'circle'),
    'e':     (0.355, 0.910, 0.030, 0.030, 'circle'),
    'r':     (0.435, 0.910, 0.030, 0.030, 'circle'),
    # 蓝色长按键
    'ctrl':  (0.650, 0.790, 0.085, 0.025, 'rect'),
    'shift': (0.650, 0.855, 0.085, 0.025, 'rect'),
    'tab':   (0.650, 0.920, 0.085, 0.025, 'rect'),
}

# 特殊键映射
SPECIAL_KEY_MAP = {
    keyboard.Key.space: 'space',
    keyboard.Key.tab: 'tab',
    keyboard.Key.shift: 'shift',
    keyboard.Key.shift_l: 'shift',
    keyboard.Key.shift_r: 'shift',
    keyboard.Key.ctrl: 'ctrl',
    keyboard.Key.ctrl_l: 'ctrl',
    keyboard.Key.ctrl_r: 'ctrl',
}


class BubbleLabel(QLabel):
    """对话气泡标签"""
    font_name = "Microsoft YaHei"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFont(QFont(self.font_name, 10))
        self.setAlignment(Qt.AlignCenter)
        self.hide()
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.hide)

    def show_text(self, text, duration=2000):
        self.setText(text)
        self.adjustSize()
        self.show()
        self.timer.start(duration)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.setBrush(QColor(255, 255, 255, 240))
        painter.setPen(QColor(200, 200, 200))
        painter.drawRoundedRect(rect, 12, 12)
        painter.setBrush(QColor(255, 255, 255, 240))
        painter.setPen(Qt.NoPen)
        tail_x = rect.width() // 2
        tail_y = rect.height() - 2
        tail = QPolygon([
            QPoint(tail_x - 8, tail_y),
            QPoint(tail_x + 8, tail_y),
            QPoint(tail_x, tail_y + 8)
        ])
        painter.drawPolygon(tail)
        painter.setPen(QColor(51, 51, 51))
        painter.setFont(self.font())
        text_rect = rect.adjusted(10, 5, -10, -10)
        painter.drawText(text_rect, Qt.AlignCenter, self.text())


class PetWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("desktop_pet")  # 窗口标题，用于FindWindow
        self.scale = 1.0
        self.base_size = 280
        self.is_top = True
        self.is_animating = False
        self.animation_index = 0
        self.drag_pos = None
        self.drag_started = False

        # 常态动画状态
        self.blink_progress = 0.0      # 0=完全睁眼, 1=完全闭眼
        self.blink_phase = 'idle'      # idle, closing, closed, opening
        self.blink_timer_val = 0
        self.breath_time = 0.0         # 呼吸动画时间
        self.idle_offset_y = 0.0       # 垂直浮动偏移
        self.idle_sway_x = 0.0         # 左右摆动偏移

        # 键盘高亮状态
        self.pressed_keys = set()
        self.key_highlights = {}       # {键名: 高亮强度 0~1}

        # 鼠标指针状态
        self.cursor_pos = QPoint(0, 0)  # 相对于窗口的坐标
        self.cursor_visible = True

        self.init_ui()
        self.init_menu()
        self.init_tray()
        self.init_idle_animation()
        self.init_input_listeners()

        self.bubble = BubbleLabel()

    def init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.original_pixmap = QPixmap(resource_path("character.png"))
        self.img_size = self.original_pixmap.width()  # 正方形图片

        self.update_pet_size()
        self.move(300, 300)

    def update_pet_size(self):
        size = int(self.base_size * self.scale)
        self.setFixedSize(size, size)

    def init_menu(self):
        self.menu = QMenu(self)

        size_menu = self.menu.addMenu("调整大小")
        for s in [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]:
            action = QAction(f"{int(s*100)}%", self)
            action.triggered.connect(lambda checked, sc=s: self.set_scale(sc))
            size_menu.addAction(action)

        self.top_action = QAction("取消置顶", self)
        self.top_action.triggered.connect(self.toggle_top)
        self.menu.addAction(self.top_action)

        self.autostart_action = QAction("开机自启动", self)
        self.autostart_action.setCheckable(True)
        self.autostart_action.setChecked(is_autostart_enabled())
        self.autostart_action.triggered.connect(self.toggle_autostart)
        self.menu.addAction(self.autostart_action)

        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.quit_app)
        self.menu.addAction(quit_action)

    def set_scale(self, scale):
        self.scale = scale
        self.update_pet_size()
        self.update()

    def toggle_top(self):
        self.is_top = not self.is_top
        if self.is_top:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            self.top_action.setText("取消置顶")
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
            self.top_action.setText("置顶显示")
        self.show()

    def toggle_autostart(self, checked):
        success = set_autostart(checked)
        if not success:
            self.autostart_action.setChecked(not checked)

    def init_tray(self):
        tray_icon = QPixmap(resource_path("icon.ico"))
        self.tray = QSystemTrayIcon(QIcon(tray_icon), self)

        tray_menu = QMenu()
        show_action = tray_menu.addAction("显示绫华")
        show_action.triggered.connect(self.show_pet)
        hide_action = tray_menu.addAction("隐藏绫华")
        hide_action.triggered.connect(self.hide_pet)
        tray_menu.addSeparator()
        tray_autostart = tray_menu.addAction("开机自启动")
        tray_autostart.setCheckable(True)
        tray_autostart.setChecked(is_autostart_enabled())
        tray_autostart.triggered.connect(self.toggle_autostart)
        tray_menu.addSeparator()
        tray_quit = tray_menu.addAction("退出")
        tray_quit.triggered.connect(self.quit_app)

        self.tray.setContextMenu(tray_menu)
        self.tray.activated.connect(self.tray_activated)
        self.tray.setToolTip("神里绫华 · 桌面宠物")
        self.tray.show()

    def tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            if self.isVisible():
                self.hide_pet()
            else:
                self.show_pet()

    def show_pet(self):
        self.show()
        self.activateWindow()

    def hide_pet(self):
        self.hide()


    # ===== Windows消息处理（单实例激活） =====
    def quit_app(self):
        self.tray.hide()
        try:
            self.kb_listener.stop()
            self.mouse_listener.stop()
        except Exception:
            pass
        QApplication.quit()

    def show_bubble(self):
        text = random.choice(DIALOGUES)
        duration = max(2000, 2000 + len(text) * 100)
        bubble_x = self.x() + self.width() // 2 - self.bubble.width() // 2
        bubble_y = self.y() - self.bubble.height() - 10
        self.bubble.move(bubble_x, bubble_y)
        self.bubble.show_text(text, duration)

    # ===== 常态动画 =====
    def init_idle_animation(self):
        self.idle_timer = QTimer(self)
        self.idle_timer.timeout.connect(self.update_idle_frame)
        self.idle_timer.start(33)  # ~30fps

    def update_idle_frame(self):
        dt = 0.033
        self.breath_time += dt

        # 呼吸浮动（上下）
        breath_amp = 2.0  # 像素
        self.idle_offset_y = math.sin(self.breath_time * 1.5) * breath_amp * self.scale

        # 轻微左右摆动
        sway_amp = 1.0
        self.idle_sway_x = math.sin(self.breath_time * 0.8) * sway_amp * self.scale

        # 眨眼逻辑
        self.blink_timer_val += dt
        if self.blink_phase == 'idle':
            # 随机3~6秒眨一次眼
            if self.blink_timer_val > random.uniform(3.0, 6.0):
                self.blink_phase = 'closing'
                self.blink_timer_val = 0
        elif self.blink_phase == 'closing':
            # 闭眼过程 0.1秒
            self.blink_progress = min(1.0, self.blink_progress + dt / 0.1)
            if self.blink_progress >= 1.0:
                self.blink_phase = 'closed'
                self.blink_timer_val = 0
        elif self.blink_phase == 'closed':
            # 闭眼停留 0.08秒
            if self.blink_timer_val > 0.08:
                self.blink_phase = 'opening'
                self.blink_timer_val = 0
        elif self.blink_phase == 'opening':
            # 睁眼过程 0.15秒
            self.blink_progress = max(0.0, self.blink_progress - dt / 0.15)
            if self.blink_progress <= 0.0:
                self.blink_progress = 0.0
                self.blink_phase = 'idle'
                self.blink_timer_val = 0

        # 按键高亮衰减
        decay = dt * 4.0
        keys_to_remove = []
        for key, intensity in self.key_highlights.items():
            new_val = intensity - decay
            if new_val <= 0:
                keys_to_remove.append(key)
            else:
                self.key_highlights[key] = new_val
        for key in keys_to_remove:
            del self.key_highlights[key]

        self.update()

    # ===== 全局键鼠监听 =====
    def init_input_listeners(self):
        # 键盘监听
        self.kb_listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )
        self.kb_listener.daemon = True
        self.kb_listener.start()

        # 鼠标监听
        self.mouse_listener = mouse.Listener(
            on_move=self.on_mouse_move,
            on_click=self.on_mouse_click
        )
        self.mouse_listener.daemon = True
        self.mouse_listener.start()

    def on_key_press(self, key):
        key_name = None
        if hasattr(key, 'char') and key.char:
            key_name = key.char.lower()
        elif key in SPECIAL_KEY_MAP:
            key_name = SPECIAL_KEY_MAP[key]

        if key_name and key_name in KEY_CONFIG:
            self.pressed_keys.add(key_name)
            self.key_highlights[key_name] = 1.0

    def on_key_release(self, key):
        key_name = None
        if hasattr(key, 'char') and key.char:
            key_name = key.char.lower()
        elif key in SPECIAL_KEY_MAP:
            key_name = SPECIAL_KEY_MAP[key]

        if key_name and key_name in self.pressed_keys:
            self.pressed_keys.discard(key_name)

    def on_mouse_move(self, x, y):
        # 获取屏幕尺寸
        screen = QApplication.primaryScreen().geometry()
        screen_w = screen.width()
        screen_h = screen.height()

        # 将屏幕坐标映射到窗口内的相对位置
        # 鼠标在屏幕上的位置比例
        rx = x / screen_w
        ry = y / screen_h

        # 映射到窗口范围内（留出边距，不让指针跑出角色区域）
        margin = 0.05
        cursor_x = int((margin + rx * (1.0 - 2 * margin)) * self.width())
        cursor_y = int((margin + ry * (1.0 - 2 * margin)) * self.height())

        # 限制在窗口范围内
        cursor_x = max(0, min(self.width() - 1, cursor_x))
        cursor_y = max(0, min(self.height() - 1, cursor_y))

        self.cursor_pos = QPoint(cursor_x, cursor_y)

    def on_mouse_click(self, x, y, button, pressed):
        pass

    # ===== 绘制 =====
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        w = self.width()
        h = self.height()

        # 应用呼吸偏移
        painter.translate(self.idle_sway_x, self.idle_offset_y)

        # 绘制角色图片
        scaled_pixmap = self.original_pixmap.scaled(
            w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        painter.drawPixmap(0, 0, scaled_pixmap)

        # 绘制键盘按键高亮
        self.draw_key_highlights(painter, w, h)

        # 绘制鼠标指针
        self.draw_mouse_cursor(painter)

        # 绘制眨眼效果（在眼睛位置绘制上眼皮）
        self.draw_blink(painter, w, h)

    def draw_key_highlights(self, painter, w, h):
        for key_name, intensity in self.key_highlights.items():
            if key_name not in KEY_CONFIG:
                continue
            cx, cy, rx, ry, ktype = KEY_CONFIG[key_name]
            px = cx * w
            py = cy * h
            prx = rx * w
            pry = ry * h

            # 高亮颜色：白色发光效果
            alpha = int(180 * intensity)
            gradient = QRadialGradient(px, py, max(prx, pry))
            gradient.setColorAt(0, QColor(255, 255, 255, alpha))
            gradient.setColorAt(0.6, QColor(255, 255, 255, int(alpha * 0.4)))
            gradient.setColorAt(1, QColor(255, 255, 255, 0))

            painter.setBrush(QBrush(gradient))
            painter.setPen(Qt.NoPen)

            if ktype == 'circle':
                painter.drawEllipse(QPoint(int(px), int(py)), int(prx * 1.3), int(pry * 1.3))
            else:
                rect = QRect(
                    int(px - prx * 1.2),
                    int(py - pry * 1.5),
                    int(prx * 2.4),
                    int(pry * 3.0)
                )
                painter.drawRoundedRect(rect, 8, 8)

    def draw_mouse_cursor(self, painter):
        if not self.cursor_visible:
            return
        x = self.cursor_pos.x()
        y = self.cursor_pos.y()

        # 绘制白色鼠标指针（箭头形状）
        cursor_size = int(16 * self.scale)
        if cursor_size < 6:
            cursor_size = 6

        painter.setBrush(QColor(255, 255, 255, 220))
        painter.setPen(QPen(QColor(60, 60, 60, 200), 1))

        # 箭头形状
        cursor = QPolygon([
            QPoint(x, y),
            QPoint(x, y + cursor_size),
            QPoint(x + cursor_size // 3, y + cursor_size * 2 // 3),
            QPoint(x + cursor_size // 2, y + cursor_size),
            QPoint(x + cursor_size * 2 // 3, y + cursor_size * 5 // 6),
            QPoint(x + cursor_size * 2 // 3, y + cursor_size * 2 // 3),
        ])
        painter.drawPolygon(cursor)

    def draw_blink(self, painter, w, h):
        if self.blink_progress <= 0.01:
            return

        # 眼睛位置（相对坐标）
        eyes = [
            (0.355, 0.550, 0.065, 0.050),  # 左眼
            (0.545, 0.550, 0.065, 0.050),  # 右眼
        ]

        # 肤色（从图片中提取的近似肤色）
        skin_color = QColor(255, 235, 225, 255)

        for ex, ey, ew, eh in eyes:
            eye_x = ex * w
            eye_y = ey * h
            eye_w = ew * w
            eye_h = eh * h

            # 上眼皮从上方盖下来
            lid_height = eye_h * self.blink_progress
            if lid_height < 1:
                continue

            # 绘制上眼皮（肤色椭圆）
            painter.setBrush(skin_color)
            painter.setPen(Qt.NoPen)

            lid_rect = QRect(
                int(eye_x - eye_w),
                int(eye_y - eye_h * 0.8),
                int(eye_w * 2),
                int(lid_height + eye_h * 0.3)
            )
            # 用Chord模式绘制上半部分椭圆作为眼皮
            painter.drawChord(lid_rect, 0, 180 * 16)

            # 绘制眼线（上眼睑的黑线）
            if self.blink_progress > 0.3:
                painter.setPen(QPen(QColor(30, 30, 40), max(1, int(1.5 * self.scale))))
                painter.setBrush(Qt.NoBrush)
                line_y = int(eye_y - eye_h * 0.5 + lid_height * 0.5)
                painter.drawArc(
                    int(eye_x - eye_w * 0.8),
                    int(line_y - eye_h * 0.3),
                    int(eye_w * 1.6),
                    int(eye_h * 0.6),
                    0, 180 * 16
                )

    # ===== 互动动画 =====
    def play_animation(self):
        if self.is_animating:
            return
        self.is_animating = True
        animations = [self.anim_jump, self.anim_squash, self.anim_shake]
        anim_func = animations[self.animation_index % len(animations)]
        self.animation_index += 1
        anim_func()
        self.show_bubble()

    def anim_jump(self):
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(400)
        start_pos = self.pos()
        jump_height = 60
        self.anim.setKeyValueAt(0, start_pos)
        self.anim.setKeyValueAt(0.5, QPoint(start_pos.x(), start_pos.y() - jump_height))
        self.anim.setKeyValueAt(1, start_pos)
        self.anim.setEasingCurve(QEasingCurve.OutQuad)
        self.anim.finished.connect(self.on_anim_finished)
        self.anim.start()

    def anim_squash(self):
        original_geom = self.geometry()
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(500)
        w, h = original_geom.width(), original_geom.height()
        cx = original_geom.x() + w // 2
        bottom = original_geom.y() + h
        squashed = QRect(cx - int(w * 1.2) // 2, bottom - int(h * 0.6),
                         int(w * 1.2), int(h * 0.6))
        stretched = QRect(cx - int(w * 0.85) // 2, bottom - int(h * 1.15),
                          int(w * 0.85), int(h * 1.15))
        self.anim.setKeyValueAt(0, original_geom)
        self.anim.setKeyValueAt(0.4, squashed)
        self.anim.setKeyValueAt(0.7, stretched)
        self.anim.setKeyValueAt(1, original_geom)
        self.anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.anim.finished.connect(self.on_anim_finished)
        self.anim.start()

    def anim_shake(self):
        self.anim = QPropertyAnimation(self, b"pos")
        self.anim.setDuration(500)
        start_pos = self.pos()
        shake_dist = 15
        self.anim.setKeyValueAt(0, start_pos)
        self.anim.setKeyValueAt(0.1, QPoint(start_pos.x() - shake_dist, start_pos.y()))
        self.anim.setKeyValueAt(0.3, QPoint(start_pos.x() + shake_dist, start_pos.y()))
        self.anim.setKeyValueAt(0.5, QPoint(start_pos.x() - shake_dist, start_pos.y()))
        self.anim.setKeyValueAt(0.7, QPoint(start_pos.x() + shake_dist, start_pos.y()))
        self.anim.setKeyValueAt(0.9, QPoint(start_pos.x() - shake_dist, start_pos.y()))
        self.anim.setKeyValueAt(1, start_pos)
        self.anim.setEasingCurve(QEasingCurve.Linear)
        self.anim.finished.connect(self.on_anim_finished)
        self.anim.start()

    def on_anim_finished(self):
        self.is_animating = False

    # ===== 鼠标事件 =====
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            self.drag_started = False
            event.accept()
        elif event.button() == Qt.RightButton:
            self.menu.exec_(event.globalPos())
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_pos:
            moved = (event.globalPos() - (self.frameGeometry().topLeft() + self.drag_pos)).manhattanLength()
            if moved > 5:
                self.drag_started = True
            self.move(event.globalPos() - self.drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drag_pos:
            if not self.drag_started:
                self.play_animation()
            self.drag_pos = None
            self.drag_started = False
            event.accept()

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            self.scale = min(2.5, self.scale + 0.1)
        else:
            self.scale = max(0.3, self.scale - 0.1)
        self.update_pet_size()
        self.update()
        event.accept()


def main():
    global _single_guard

    # 单实例守卫
    _single_guard = SingleInstanceGuard("desktop_pet")
    if not _single_guard.acquire():
        # 已有实例在运行，退出当前进程
        print("Another instance is already running, exiting...")
        sys.exit(0)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    pet = PetWidget()
    pet.show()

    # 启动单实例激活监听（使用信号连接，线程安全）
    def on_activate():
        # 如果当前没有置顶，临时置顶一次拉到前台，然后恢复
        if not pet.is_top:
            pet.setWindowFlags(pet.windowFlags() | Qt.WindowStaysOnTopHint)
            pet.show()
            # 先置顶拉到前台
            bring_to_front(pet)
            # 延时恢复窗口标志（非置顶）
            QTimer.singleShot(200, lambda: pet.setWindowFlags(pet.windowFlags() & ~Qt.WindowStaysOnTopHint) or pet.show())
        else:
            bring_to_front(pet)

    _single_guard.activated.connect(on_activate)
    _single_guard.start_activation_server()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
