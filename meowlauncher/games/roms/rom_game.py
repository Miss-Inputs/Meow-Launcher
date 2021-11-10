import os
import tempfile
from typing import Optional, cast

from meowlauncher import launchers, metadata
from meowlauncher.emulated_platform import EmulatedPlatform
from meowlauncher.emulator import StandardEmulator

from .rom import ROM, CompressedROM


class RomGame():
	def __init__(self, rom: ROM, system_name: str, system: EmulatedPlatform):
		self.rom = rom
		self.metadata = metadata.Metadata()
		self.system_name = self.metadata.platform = system_name
		self.system = system
		self.metadata.categories = []
		self.filename_tags: list[str] = []

		self.emulator: Optional[StandardEmulator] = None
		self.launch_params: Optional[launchers.LaunchParams] = None

		self.subroms = []
		self.software_lists = None
		self.exception_reason = None

	def make_launcher(self) -> None:
		params = self.launch_params

		if self.rom.is_compressed:
			rom = cast(CompressedROM, self.rom)
			if rom.extension not in self.emulator.supported_compression:
				temp_extraction_folder = os.path.join(tempfile.gettempdir(), 'meow-launcher-' + launchers.make_filename(self.rom.name))

				extracted_path = os.path.join(temp_extraction_folder, rom.inner_filename)
				params = params.replace_path_argument(extracted_path)
				params = params.prepend_command(launchers.LaunchParams('7z', ['x', '-o' + temp_extraction_folder, str(self.rom.path)]))
				params = params.append_command(launchers.LaunchParams('rm', ['-rf', temp_extraction_folder]))
		else:
			params = params.replace_path_argument(str(self.rom.path))

		name = self.rom.name
		if self.rom.ignore_name and self.metadata.names:
			name = self.metadata.names.get('Name', list(self.metadata.names.values())[0])
		launchers.make_launcher(params, name, self.metadata, 'ROM', self.rom.path)
