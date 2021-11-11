import os
from typing import Any

from meowlauncher.config.system_config import system_configs
from meowlauncher.games.pc_common_metadata import look_for_icon_next_to_file

from .pc import App

dos_config = system_configs.get('DOS')

class DOSApp(App):
	def __init__(self, info: dict[str, Any]):
		super().__init__(info)
		if self.is_on_cd:
			self.path = self.path.replace('/', '\\')

	@property
	def is_valid(self) -> bool:
		if self.is_on_cd:
			if not self.cd_path:
				return False
			return os.path.isfile(self.cd_path) #TODO: Use pycdlib to see if it exists on the CD
		return os.path.isfile(self.path)

	def get_fallback_name(self) -> str:
		if self.is_on_cd:
			if not self.cd_path:
				raise KeyError('cd_path is mandatory if is_on_cd is true')
			return os.path.splitext(os.path.basename(self.cd_path))[0]
		return os.path.basename(os.path.dirname(self.path)) if dos_config.options['use_directory_as_fallback_name'] else super().get_fallback_name()

	def additional_metadata(self) -> None:
		basename = self.path.split('\\')[-1] if self.is_on_cd else os.path.basename(self.path)
		self.metadata.specific_info['Executable-Name'] = basename
		self.metadata.extension = basename.split('.', 1)[-1].lower()
		if not self.is_on_cd:
			icon = look_for_icon_next_to_file(self.path)
			if icon:
				self.metadata.images['Icon'] = icon
