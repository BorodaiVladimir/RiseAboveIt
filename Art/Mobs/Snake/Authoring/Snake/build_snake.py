"""Blender entry point for the current snake revision; v1 is archived separately."""
import runpy
from pathlib import Path
runpy.run_path(str(Path(__file__).with_name('build_snake_v4.py')), run_name='__main__')
