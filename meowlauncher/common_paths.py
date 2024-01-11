from pathlib import Path

#TODO: Get this in a less hardcody cross-platform way, I guess
config_dir = Path('~/.config/Meow Launcher').expanduser()
data_dir = Path('~/.local/share/Meow Launcher').expanduser()
cache_dir = Path('~/.cache/Meow Launcher').expanduser()
