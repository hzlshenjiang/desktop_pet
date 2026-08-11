"""
单实例守卫模块 - 基于 QSharedMemory + QLocalServer
参考 QZCAD 的实现方式
"""
import sys
import os
from PyQt5.QtCore import QSharedMemory
from PyQt5.QtNetwork import QLocalServer, QLocalSocket
from PyQt5.QtWidgets import QApplication


class SingleInstanceGuard:
    """单实例守卫器，防止同一应用多次启动"""
    
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
        self.server_name = f"{app_name}_{user_id}"
        
        self.shared_memory = QSharedMemory(self.shared_memory_key)
        self.local_server = QLocalServer()
        
        self.is_primary = False
        self._cleanup_stale()
    
    def _cleanup_stale(self):
        """清理过期的共享内存和服务器"""
        # 尝试附加到已存在的共享内存
        if self.shared_memory.attach():
            # 如果能附加，说明可能有残留，尝试释放
            self.shared_memory.detach()
        
        # 移除可能残留的本地服务器
        QLocalServer.removeServer(self.server_name)
    
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
            
            # 启动本地服务器用于接收激活请求
            if self.local_server.listen(self.server_name):
                self.local_server.newConnection.connect(self._on_new_connection)
                return True
            else:
                # 服务器启动失败，清理并返回
                self.shared_memory.detach()
                return False
        else:
            # 创建失败，说明已有实例
            self.is_primary = False
            
            # 尝试连接到已有实例并发送激活请求
            self._activate_existing_instance()
            return False
    
    def _activate_existing_instance(self):
        """通知已有实例激活窗口"""
        socket = QLocalSocket()
        socket.connectToServer(self.server_name)
        
        if socket.waitForConnected(800):
            # 发送激活信号
            socket.write(b"ACTIVATE")
            socket.flush()
            socket.waitForBytesWritten(800)
            socket.disconnectFromServer()
    
    def _on_new_connection(self):
        """处理新的连接请求"""
        while self.local_server.hasPendingConnections():
            connection = self.local_server.nextPendingConnection()
            # 读取消息
            if connection.waitForReadyRead(500):
                message = connection.readLine()
                if message.data() == b"ACTIVATE":
                    # 发送信号激活主窗口
                    self._send_activate_signal()
            connection.disconnectFromServer()
            connection.deleteLater()
    
    def _send_activate_signal(self):
        """发送激活信号到主应用"""
        # 通过 QMetaObject 调用主窗口的 bring_to_front 方法
        # 这里使用 QCoreApplication  postEvent 机制
        from PyQt5.QtCore import QCoreApplication, QEvent, pyqtSignal
        from PyQt5.QtGui import QHideEvent, QShowEvent
        
        # 发送自定义事件激活窗口
        class ActivateEvent(QEvent):
            Type = QEvent.Type(QEvent.registerEventType())
            
            def __init__(self):
                super().__init__(ActivateEvent.Type)
        
        QCoreApplication.postEvent(QApplication.instance(), ActivateEvent())
    
    def release(self):
        """释放单实例锁"""
        if self.is_primary:
            self.local_server.close()
            self.shared_memory.detach()
    
    def __del__(self):
        self.release()


def check_single_instance(app_name="desktop_pet"):
    """
    检查单实例的便捷函数
    
    Returns:
        tuple: (is_primary, guard) 
            - is_primary: 是否是本实例
            - guard: 守卫对象，主实例需要保存引用防止被释放
    """
    guard = SingleInstanceGuard(app_name)
    is_primary = guard.acquire()
    return is_primary, guard
