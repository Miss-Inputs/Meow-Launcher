import os
import tempfile
from typing import Optional, Union

from meowlauncher import launchers, metadata
from .rom import FileROM, FolderROM
from meowlauncher.info import emulator_info, system_info


class RomGame():
	def __init__(self, rom: Union[FileROM, FolderROM], system_name: str, system: system_info.SystemInfo):
		self.rom = rom
		self.metadata = metadata.Metadata()
		self.system_name = self.metadata.platform = system_name
		self.system = system
		self.metadata.categories = []
		self.filename_tags = []

		self.emulator: Optional[emulator_info.Emulator] = None
		self.launch_params: Optional[launchers.LaunchParams] = None

		self.subroms = []
		self.software_lists = None
		self.exception_reason = None

	def make_launcher(self) -> None:
		params = self.launch_params

		if self.rom.is_compressed and (self.rom.original_extension not in self.emulator.supported_compression):
			temp_extraction_folder = os.path.join(tempfile.gettempdir(), 'meow-launcher-' + launchers.make_filename(self.rom.name))

			extracted_path = os.path.join(temp_extraction_folder, self.rom.compressed_entry)
			params = params.replace_path_argument(extracted_path)
			params = params.prepend_command(launchers.LaunchParams('7z', ['x', '-o' + temp_extraction_folder, self.rom.path]))
			params = params.append_command(launchers.LaunchParams('rm', ['-rf', temp_extraction_folder]))
		else:
			params = params.replace_path_argument(self.rom.path)

		name = self.rom.name
		if self.rom.ignore_name and self.metadata.names:
			name = self.metadata.names.get('Name', list(self.metadata.names.values())[0])
		launchers.make_launcher(params, name, self.metadata, 'ROM', self.rom.path)
