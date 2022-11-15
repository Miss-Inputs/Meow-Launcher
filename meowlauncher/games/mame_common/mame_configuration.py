import os
import re
from collections.abc import Mapping, Sequence
from pathlib import Path

image_types = {'ico', 'png', 'jpg', 'bmp'}

class MAMEConfiguration():
	def __init__(self, core_config_path: Path|None=None, ui_config_path: Path|None=None) -> None:
		if not core_config_path:
			core_config_path = Path('~/.mame/mame.ini').expanduser()
		self.core_config = parse_mame_config_file(core_config_path)
		if not ui_config_path:
			ui_config_path = Path('~/.mame/ui.ini').expanduser()
		self.ui_config = parse_mame_config_file(ui_config_path)
		self._icons = None

	def get_image(self, config_key: str, machine_or_list_name: str, software_name: str | None=None) -> Path | None:
		for directory in self.ui_config.get(config_key, ()):
			basename = Path(directory, machine_or_list_name)
			if software_name:
				basename = basename.joinpath(software_name)
			for ext in image_types:
				path = basename.with_suffix(os.path.extsep + ext)
				if path.is_file():
					return path
		return None

_mame_config_comment = re.compile(r'#.+$')
_mame_config_line = re.compile(r'^(?P<key>\w+)\s+(?P<value>[^;]+|"[^"]+")$')
def parse_mame_config_file(path: Path) -> Mapping[str, Sequence[str]]:
	settings = {}

	with path.open('rt', encoding='utf-8-sig') as f:
		for line in f:
			line = _mame_config_comment.sub('', line)
			line = line.strip()

			if not line:
				continue

			match = _mame_config_line.match(line)
			if match:
				key = match['key']
				values = match['value']
				if values[0] == '"' and values[-1] == '"':
					values = values[1:-1]
				settings[key] = values.split(';')
	return settings
