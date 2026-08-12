"""
单实例守卫模块 - 基于 PID 文件 + 进程检查
- PID文件记录主实例PID
- OpenProcess 检查PID是否存活，区分活跃实例与残留
- 文件轮询：通过 QTimer.singleShot 递归轮询传递激活信号
"""
import os
import tempfile
import ctypes
from PyQt5.QtCore import QObject, pyqtSignal, QTimer


class SingleInstanceGuard(QObject):
    """单实例守卫器，防止同一应用多次启动"""

    activated = pyqtSignal()

    def __init__(self, app_name="desktop_pet", user_id=None):
        super().__init__()
        if user_id is None:
            try:
                user_id = os.getlogin()
            except Exception:
                import getpass
                user_id = getpass.getuser()

        self.pid_file = os.path.join(tempfile.gettempdir(),
                                     f"{app_name}_{user_id}.pid")
        self.request_file = os.path.join(tempfile.gettempdir(),
                                         f"{app_name}_{user_id}_activate.txt")
        self.is_primary = False
        self._pid = os.getpid()

    def _is_process_alive(self, pid):
        """检查进程是否存活（Windows OpenProcess）"""
        try:
            kernel32 = ctypes.windll.kernel32
            kernel32.OpenProcess.restype = ctypes.c_void_p
            handle = kernel32.OpenProcess(0x400, False, pid)
            if handle:
                kernel32.CloseHandle(handle)
                return True
            return False
        except:
            return False

    def acquire(self):
        """检查是否已有实例，并获取单实例锁"""
        if os.path.exists(self.pid_file):
            try:
                with open(self.pid_file, 'r') as f:
                    old_pid = int(f.read().strip())
                alive = self._is_process_alive(old_pid)
                if alive:
                    self.is_primary = False
                    self._activate_existing_instance()
                    return False
            except:
                pass
            try:
                os.remove(self.pid_file)
            except:
                pass

        try:
            with open(self.pid_file, 'w') as f:
                f.write(str(self._pid))
            self.is_primary = True
            return True
        except Exception:
            self.is_primary = False
            return False

    def _activate_existing_instance(self):
        """通过文件写入激活请求"""
        try:
            with open(self.request_file, 'w') as f:
                f.write("ACTIVATE")
        except Exception as e:
            print(f"[SingleInstance] 激活请求失败: {e}")

    def start_activation_server(self):
        """启动激活监听（通过QTimer递归轮询文件）"""
        if not self.is_primary:
            return

        try:
            if os.path.exists(self.request_file):
                os.remove(self.request_file)
        except:
            pass

        self._poll()

    def _poll(self):
        """递归轮询激活请求文件"""
        self._poll_activation_request()
        QTimer.singleShot(500, self._poll)

    def _poll_activation_request(self):
        """轮询检查激活请求文件"""
        try:
            if os.path.exists(self.request_file):
                with open(self.request_file, 'r') as f:
                    content = f.read().strip()
                if content == "ACTIVATE":
                    try:
                        os.remove(self.request_file)
                    except:
                        pass
                    self.activated.emit()
        except:
            pass

    def release(self):
                    try:
                            if os.path.exists(self.pid_file):
                                    with open(self.pid_file, 'r') as f:
                                            pid = int(f.read().strip())
                                    if pid == self._pid:
                                            os.remove(self.pid_file)
                    except:
                            pass
                    # 仅主实例清理请求文件（非主实例的release会误删刚写入的激活请求）
                    if self.is_primary:
                            try:
                                    if os.path.exists(self.request_file):
                                            os.remove(self.request_file)
                            except:
                                    pass

    def __del__(self):
        self.release()