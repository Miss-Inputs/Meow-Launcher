from pathlib import Path


#TODO: Get this in a less hardcody cross-platform way, I guess
config_dir = Path('~/.config/MeowLauncher').expanduser()
data_dir = Path('~/.local/share/MeowLauncher').expanduser()
cache_dir = Path('~/.cache/MeowLauncher').expanduser()
