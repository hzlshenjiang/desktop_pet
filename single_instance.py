"""
防止多开的锁文件管理器
"""
import os
import sys
import time
import ctypes
import threading

class SingleInstanceGuard:
    """
    防止程序多开的守卫类
    使用锁文件方式，确保同一时间只有一个实例运行
    """
    
    def __init__(self, name="desktop_pet"):
        self.name = name
        self.lock_file = None
        self.lock_path = None
        
    def acquire(self):
        """
        尝试获取锁，返回True表示成功（可以启动），False表示已存在实例
        """
        try:
            # 确定锁文件路径
            if getattr(sys, 'frozen', False):
                # PyInstaller打包后的路径
                base_dir = os.path.dirname(sys.executable)
            else:
                # 开发环境路径
                base_dir = os.path.dirname(os.path.abspath(__file__))
            
            self.lock_path = os.path.join(base_dir, f'.{self.name}.lock')
            
            # 尝试创建锁文件
            self.lock_file = open(self.lock_path, 'w')
            self.lock_file.write(f'{os.getpid()}\n')
            self.lock_file.write(f'{time.time()}\n')
            self.lock_file.flush()
            
            # 尝试获取排他锁（跨平台兼容）
            if os.name == 'nt':
                # Windows: 使用ctypes获取文件锁
                handle = ctypes.windll.kernel32.CreateFileW(
                    self.lock_path,
                    0,  # 共享模式：不共享
                    3,  # 访问模式：无（仅用于锁）
                    None,
                    1,  # 创建模式：打开现有
                    0,  # 文件属性
                    None
                )
                if handle == -1:  # INVALID_HANDLE_VALUE
                    self.lock_file.close()
                    self.lock_file = None
                    return False
                # 存储句柄用于后续释放
                self._handle = handle
            else:
                # Unix: 使用flock
                import fcntl
                try:
                    fcntl.flock(self.lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except (IOError, OSError):
                    self.lock_file.close()
                    self.lock_file = None
                    return False
            
            return True
            
        except Exception as e:
            print(f"锁文件创建失败: {e}")
            if self.lock_file:
                self.lock_file.close()
                self.lock_file = None
            return False
    
    def release(self):
        """释放锁"""
        try:
            if hasattr(self, '_handle'):
                ctypes.windll.kernel32.CloseHandle(self._handle)
            
            if self.lock_file:
                self.lock_file.close()
                self.lock_file = None
            
            # 删除锁文件
            if self.lock_path and os.path.exists(self.lock_path):
                os.remove(self.lock_path)
                
        except Exception as e:
            print(f"锁文件释放失败: {e}")
    
    def __enter__(self):
        return self.acquire()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False

# 全局守卫实例
_guard = None

def get_guard():
    """获取全局守卫实例"""
    global _guard
    if _guard is None:
        _guard = SingleInstanceGuard()
    return _guard

def check_single_instance():
    """
    检查是否已经是单实例
    返回True表示可以启动，False表示已有实例在运行
    """
    guard = get_guard()
    if guard.acquire():
        print("单实例检查通过")
        return True
    else:
        print("检测到已有实例在运行，退出")
        return False

def release_instance():
    """释放实例锁"""
    guard = get_guard()
    guard.release()

def cleanup_lock():
    """清理锁文件（用于异常退出时）"""
    try:
        if os.path.exists(_guard.lock_path if _guard else None):
            os.remove(_guard.lock_path)
    except:
        pass
