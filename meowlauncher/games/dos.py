import os
from collections.abc import Mapping
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Any

from meowlauncher.config.platform_config import platform_configs
from meowlauncher.games.common.pc_common_metadata import \
    look_for_icon_for_file

from .pc import App

if TYPE_CHECKING:
	from meowlauncher.config_types import PlatformConfig

dos_config = platform_configs.get('DOS')

class DOSApp(App):
	def __init__(self, info: Mapping[str, Any], platform_config: 'PlatformConfig'):
		super().__init__(info, platform_config)
		if self.is_on_cd:
			self.path = self.path.replace('/', '\\')

	@property
	def is_valid(self) -> bool:
		if self.is_on_cd:
			if not self.cd_path:
				return False
			return self.cd_path.is_file() #TODO: Use pycdlib to see if it exists on the CD
		return os.path.isfile(self.path)

	@property
	def fallback_name(self) -> str:
		if self.is_on_cd:
			if not self.cd_path:
				raise KeyError('cd_path is mandatory if is_on_cd is true')
			return self.cd_path.stem
		return PurePath(self.path).parent.name if dos_config.options['use_directory_as_fallback_name'] else super().fallback_name

	def additional_metadata(self) -> None:
		basename = self.path.split('\\')[-1] if self.is_on_cd else os.path.basename(self.path)
		self.metadata.specific_info['Executable Name'] = basename
		self.metadata.specific_info['Extension'] = basename.split('.', 1)[-1].lower()
		if not self.is_on_cd:
			icon = look_for_icon_for_file(Path(self.path))
			if icon:
				self.metadata.images['Icon'] = icon
