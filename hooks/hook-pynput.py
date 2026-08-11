# PyInstaller hook for pynput
# Patches the backend function to use absolute imports
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = collect_submodules('pynput')
