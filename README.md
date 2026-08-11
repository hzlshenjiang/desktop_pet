# 桌面宠物 (Desktop Pet)

一个可爱的桌面宠物应用，基于 PyQt5 开发，支持键盘/鼠标联动、眨眼动画等趣味功能。

## 功能特性

- **键盘联动**：敲击键盘时，桌宠键盘上对应按键会白色高亮发光
- **鼠标联动**：桌宠画面内的鼠标指针跟随真实鼠标移动
- **眨眼动画**：角色会每隔几秒自然眨一次眼
- **呼吸微动**：角色有轻微的上下浮动和左右摆动
- **点击互动**：点击角色触发跳跃、压扁回弹、左右抖动等动画
- **滚轮缩放**：鼠标滚轮可调整角色大小（30% ~ 250%）
- **右键菜单**：调整大小、置顶开关、开机自启动、退出
- **系统托盘**：双击托盘图标显示/隐藏，右键完整菜单
- **单实例守卫**：防止重复启动，已有实例时自动激活窗口

## 系统要求

- Windows 10/11
- Python 3.8+
- 无需安装额外运行库（打包后为单文件 EXE）

## 快速开始

### 运行预编译版本

直接双击运行 `dist/desktop_pet.exe` 即可。

### 自行编译打包

#### 1. 安装依赖

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

依赖包：
- PyQt5>=5.15.0
- pyinstaller>=5.0
- pynput>=1.7.0

#### 2. 打包命令

**方式一：双击打包脚本**
```bash
打包.bat
```

**方式二：命令行打包**
```bash
python -m PyInstaller desktop_pet.spec --clean --noconfirm
```

#### 3. 输出位置

打包完成后，EXE 文件位于：
```
dist/desktop_pet.exe
```

文件大小约 44MB，包含所有必要资源，可作为绿色版软件单独使用。

## 项目结构

```
desktop_pet/
├── desktop_pet.py      # 主程序
├── desktop_pet.spec    # PyInstaller 打包配置
├── pynput_patch.py     # 自定义键鼠监听（替代原版 pynput）
├── single_instance.py  # 单实例守卫
├── character.png       # 角色图片（2048x2048 RGBA）
├── icon.ico            # 应用图标
├── requirements.txt    # 依赖列表
├── build.py           # 打包辅助脚本
├── 打包.bat           # Windows 打包脚本
└── README.md          # 本说明文档
```

## 技术说明

### 为什么 exe 这么大？

182MB 是 PyQt5 应用的正常大小，主要因为：
- Qt5 框架本身约 120MB
- Python 运行时约 30MB
- PyQt5 Python 模块约 20MB
- 资源文件约 4MB

PyInstaller 打包 PyQt5 应用时，必须包含完整的 Qt 框架，这是 Qt 的设计决定的，无法避免。

### 打包配置说明

`desktop_pet.spec` 关键配置：

```python
datas=[
    ('character.png', '.'),  # 角色图片
    ('icon.ico', '.'),       # 应用图标
]

icon='icon.ico'  # EXE 图标
```

### pynput 替代方案

原版 pynput 在 PyInstaller 打包时会出现导入问题，本项目使用自定义的 `pynput_patch.py` 替代，基于 win32 API 实现键盘鼠标监听。

## 常见问题

### Q: 打包后 exe 图标不显示？

确保 `.spec` 文件中配置了 `icon='icon.ico'`，并清理 Windows 图标缓存：
```powershell
Remove-Item -Path "$env:LOCALAPPDATA\IconCache.db" -Force
Stop-Process -Name explorer
Start-Process explorer
```

### Q: 运行时提示 "Pixmap is a null pixmap"？

确保 `character.png` 已包含在打包配置中：
```python
datas=[
    ('character.png', '.'),
]
```

### Q: 如何修改角色图片？

替换 `character.png` 文件，要求：
- 格式：PNG（支持透明通道）
- 尺寸：建议使用 2048x2048 或更大
- 背景：透明背景

### Q: 如何修改键盘按键？

编辑 `desktop_pet.py` 中的 `KEY_CONFIG` 字典：
```python
KEY_CONFIG = {
    'Q': (0.1, 0.7, 0.08, 0.08),  # (cx, cy, rx, ry)
    # ...
}
```

坐标范围：0.0 ~ 1.0，相对于窗口大小。

## 开发说明

### 代码修改后重新打包

```bash
# 清理旧构建
rm -rf build dist

# 重新打包
python -m PyInstaller desktop_pet.spec --clean --noconfirm
```

### 测试运行（不打包）

```bash
python desktop_pet.py
```

## 许可证

MIT License

## 作者

qianxiao

---

**注意**：本项目使用 PyInstaller 打包，请勿修改打包配置中的 `datas` 字段，否则可能导致资源文件无法正确嵌入。
