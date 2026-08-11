"""
Pynput compatibility layer.
"""
import sys
import os

# Add shadow pynput to path
project_dir = os.path.dirname(os.path.abspath(__file__))
shadow_pynput = os.path.join(project_dir, 'pynput')
if os.path.exists(shadow_pynput) and shadow_pynput not in sys.path:
    sys.path.insert(0, project_dir)

from pynput import keyboard, mouse
print('Loaded pynput from:', keyboard.__file__)
