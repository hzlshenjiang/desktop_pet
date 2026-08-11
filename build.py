# PyInstaller build script for desktop_pet
# Usage: python build.py

import os
import subprocess
import sys

project_dir = r'D:\work\Project\desktop_pet'

print('Building desktop_pet.exe...')
result = subprocess.run(
    [sys.executable, '-m', 'PyInstaller', 'desktop_pet.spec', '--clean', '--noconfirm'],
    cwd=project_dir,
)
sys.exit(result.returncode)
