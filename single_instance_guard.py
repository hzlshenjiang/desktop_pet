"""
单实例守卫模块 - 基于 QSharedMemory + Python标准库socket
不使用QtNetwork，避免PyInstaller打包问题
"""
import sys
import os
import socket
import struct
from PyQt5.QtCore import QSharedMemory, QTimer


class SingleInstanceGuard:
    """单实例守卫器，防止同一应用多次启动"""
    
    # 单实例激活信号事件类型
    ACTIVATE_EVENT = 0
    
    def __init__(self, app_name="desktop_pet", user_id=None):
        """
        初始化单实例守卫
        
        Args:
            app_name: 应用标识名
            user_id: 用户标识，默认使用用户名
        """
        # 使用用户名作为 user_id，确保多用户环境下独立
        if user_id is None:
            try:
                user_id = os.getlogin()
            except:
                import getpass
                user_id = getpass.getuser()
        
        self.app_name = app_name
        self.user_id = user_id
        self.shared_memory_key = f"{app_name}_{user_id}"
        self.socket_port = self._get_socket_port()
        
        self.shared_memory = QSharedMemory(self.shared_memory_key)
        
        self.is_primary = False
        self._cleanup_stale()
    
    def _get_socket_port(self):
        """获取用于单实例通信的端口号"""
        # 使用固定端口范围，基于app_name和user_id哈希
        base_port = 19876  # 固定起始端口
        hash_val = hash(f"{self.app_name}_{self.user_id}") % 1000
        return base_port + hash_val
    
    def _cleanup_stale(self):
        """清理过期的共享内存"""
        # 尝试附加到已存在的共享内存
        if self.shared_memory.attach():
            # 如果能附加，说明可能有残留，尝试释放
            self.shared_memory.detach()
    
    def acquire(self):
        """
        尝试获取单实例锁
        
        Returns:
            bool: True 表示是本实例（主实例），False 表示已有实例在运行
        """
        # 尝试创建共享内存
        if self.shared_memory.create(1):
            # 创建成功，是本实例
            self.is_primary = True
            return True
        else:
            # 创建失败，说明已有实例
            self.is_primary = False
            
            # 尝试连接到已有实例并发送激活请求
            self._activate_existing_instance()
            return False
    
    def _activate_existing_instance(self):
        """通知已有实例激活窗口"""
        try:
            # 创建TCP socket连接到已有实例
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.8)
            sock.connect(('127.0.0.1', self.socket_port))
            sock.sendall(b"ACTIVATE")
            sock.close()
        except Exception as e:
            print(f"[SingleInstance] 激活请求失败: {e}")
    
    def start_activation_server(self, activate_callback):
        """
        启动激活监听服务器（仅主实例调用）
        
        Args:
            activate_callback: 激活回调函数
        """
        if not self.is_primary:
            return
        
        self._activate_callback = activate_callback
        
        # 启动服务器线程
        import threading
        self._server_thread = threading.Thread(target=self._listen_for_activation, daemon=True)
        self._server_thread.start()
    
    def _listen_for_activation(self):
        """监听激活请求的服务器线程"""
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(('127.0.0.1', self.socket_port))
            server.listen(1)
            server.settimeout(1.0)
            
            while True:
                try:
                    conn, addr = server.accept()
                    data = conn.recv(1024)
                    if data == b"ACTIVATE":
                        # 在主线程中调用回调
                        QTimer.singleShot(0, self._activate_callback)
                    conn.close()
                except socket.timeout:
                    continue
                except Exception:
                    break
            
            server.close()
        except Exception as e:
            print(f"[SingleInstance] 服务器启动失败: {e}")
    
    def release(self):
        """释放单实例锁"""
        if self.is_primary:
            self.shared_memory.detach()
    
    def __del__(self):
        self.release()
