import os
import re
from typing import Optional

image_types = ('ico', 'png', 'jpg', 'bmp')

class MAMEConfiguration():
	def __init__(self, core_config_path=None, ui_config_path=None) -> None:
		if not core_config_path:
			core_config_path = os.path.expanduser('~/.mame/mame.ini')
		self.core_config = parse_mame_config_file(core_config_path)
		if not ui_config_path:
			ui_config_path = os.path.expanduser('~/.mame/ui.ini')
		self.ui_config = parse_mame_config_file(ui_config_path)
		self._icons = None

	def get_image(self, config_key: str, machine_or_list_name: str, software_name: Optional[str]=None) -> Optional[str]:
		for directory in self.ui_config.get(config_key, []):
			basename = os.path.join(directory, machine_or_list_name)
			if software_name:
				basename = os.path.join(basename, software_name)
			for ext in image_types:
				path = basename + os.path.extsep + ext
				if os.path.isfile(path):
					return path
		return None

mame_config_comment = re.compile(r'#.+$')
mame_config_line = re.compile(r'^(?P<key>\w+)\s+(?P<value>.+)$')
semicolon_not_after_quotes = re.compile(r'(?!");')
def parse_mame_config_file(path: str) -> dict[str, list[str]]:
	settings: dict[str, list[str]] = {}

	with open(path, 'rt') as f:
		for line in f.readlines():
			line = mame_config_comment.sub('', line)
			line = line.strip()

			if not line:
				continue

			match = mame_config_line.match(line)
			if match:
				key = match['key']
				values = semicolon_not_after_quotes.split(match['value'])
				settings[key] = []
				for value in values:
					if value[0] == '"' and value[-1] == '"':
						value = value[1:-1]
					settings[key].append(value)
	return settings
