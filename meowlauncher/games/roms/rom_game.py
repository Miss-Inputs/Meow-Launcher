from meowlauncher import metadata
from meowlauncher.emulated_platform import EmulatedPlatform

from .rom import ROM


class RomGame():
	def __init__(self, rom: ROM, platform_name: str, platform: EmulatedPlatform):
		self.rom = rom
		self.metadata = metadata.Metadata()
		self.platform_name = self.metadata.platform = platform_name
		self.platform = platform
		self.metadata.categories = []
		self.filename_tags: list[str] = []

		self.subroms = []
		self.software_lists = None
		self.exception_reason = None
	
	@property
	def name(self) -> str:
		name = self.rom.name
		if self.rom.ignore_name and self.metadata.names:
			name = self.metadata.names.get('Name', list(self.metadata.names.values())[0])
			
		return name
