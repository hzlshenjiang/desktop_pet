"""
防止多开的锁文件管理器
简化版：只检查文件是否存在，不使用文件锁
"""
import os
import sys
import time

class SingleInstanceGuard:
    """
    防止程序多开的守卫类
    使用锁文件方式，确保同一时间只有一个实例运行
    """
    
    def __init__(self, name="desktop_pet"):
        self.name = name
        self.lock_path = None
        self.lock_file = None
        
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
            
            # 检查锁文件是否存在
            if os.path.exists(self.lock_path):
                # 锁文件存在，但可能进程已结束
                try:
                    with open(self.lock_path, 'r') as f:
                        lines = f.readlines()
                        if len(lines) >= 1:
                            pid = int(lines[0].strip())
                            # 检查进程是否还在运行
                            import subprocess
                            subprocess.run(['tasklist', '/FI', f'PID eq {pid}', '/NH'], 
                                        capture_output=True)
                            if subprocess.run(['tasklist', '/FI', f'PID eq {pid}', '/NH'],
                                           capture_output=True).returncode != 0:
                                # 进程不存在，删除旧锁文件
                                os.remove(self.lock_path)
                            else:
                                # 进程还在运行
                                return False
                except (ValueError, IOError):
                    # 锁文件格式错误，删除并重新创建
                    try:
                        os.remove(self.lock_path)
                    except:
                        pass
            
            # 创建锁文件
            self.lock_file = open(self.lock_path, 'w')
            self.lock_file.write(f'{os.getpid()}\n')
            self.lock_file.write(f'{time.time()}\n')
            self.lock_file.flush()
            
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
