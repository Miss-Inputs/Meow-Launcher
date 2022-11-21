import os
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Any

from meowlauncher.games.common.pc_common_info import look_for_icon_for_file
from meowlauncher.manually_specified_game import ManuallySpecifiedGame

if TYPE_CHECKING:
	from meowlauncher.config_types import PlatformConfig
	from collections.abc import Mapping

class DOSApp(ManuallySpecifiedGame):
	def __init__(self, info: 'Mapping[str, Any]', platform_config: 'PlatformConfig'):
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
		return PurePath(self.path).parent.name if self.platform_config.options['use_directory_as_fallback_name'] else super().fallback_name

	def additional_info(self) -> None:
		basename = self.path.split('\\')[-1] if self.is_on_cd else os.path.basename(self.path)
		self.info.specific_info['Executable Name'] = basename
		self.info.specific_info['Extension'] = basename.split('.', 1)[-1].lower()
		if not self.is_on_cd:
			icon = look_for_icon_for_file(Path(self.path))
			if icon:
				self.info.images['Icon'] = icon
