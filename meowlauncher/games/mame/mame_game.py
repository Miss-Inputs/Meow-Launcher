from meowlauncher.games.mame_common.machine import Machine
from meowlauncher.metadata import Date, Metadata
from meowlauncher.emulated_game import EmulatedGame

class MAMEGame(EmulatedGame):
	def __init__(self, machine: Machine):
		super().__init__()
		self.machine = machine
		self.metadata = Metadata()

		self._add_metadata_fields()

	@property
	def name(self) -> str:
		return self.machine.name

	def _add_metadata_fields(self) -> None:
		self._has_inited_metadata = True
		self.metadata.specific_info['Source-File'] = self.machine.source_file
		self.metadata.specific_info['Family-Basename'] = self.machine.family
		self.metadata.specific_info['Family'] = self.machine.family_name
		self.metadata.specific_info['Has-Parent'] = self.machine.has_parent

		self.metadata.release_date = Date(self.machine.xml.findtext('year'))

		self.metadata.specific_info['Number-of-Players'] = self.machine.number_of_players
		self.metadata.specific_info['Is-Mechanical'] = self.machine.is_mechanical
		self.metadata.specific_info['Dispenses-Tickets'] = self.machine.uses_device('ticket_dispenser')
		self.metadata.specific_info['Coin-Slots'] = self.machine.coin_slots
		self.metadata.specific_info['Requires-CHD'] = self.machine.requires_chds
		self.metadata.specific_info['Romless'] = self.machine.romless
		self.metadata.specific_info['Slot-Names'] = [slot.instances[0][0] for slot in self.machine.media_slots if slot.instances]
		self.metadata.specific_info['Software-Lists'] = self.machine.software_list_names
		self.metadata.series = self.machine.series
		bios = self.machine.bios
		if bios:
			self.metadata.specific_info['BIOS-Used'] = bios.basename
			self.metadata.specific_info['BIOS-Used-Full-Name'] = bios.name
		if self.machine.samples_used:
			self.metadata.specific_info['Samples-Used'] = self.machine.samples_used
		arcade_system = self.machine.arcade_system
		if arcade_system:
			self.metadata.specific_info['Arcade-System'] = arcade_system

		licensed_from = self.machine.licensed_from
		if self.machine.licensed_from:
			self.metadata.specific_info['Licensed-From'] = licensed_from

		hacked_by = self.machine.hacked_by
		if self.machine.hacked_by:
			self.metadata.specific_info['Hacked-By'] = hacked_by

		self.metadata.developer, self.metadata.publisher = self.machine.developer_and_publisher

		self.metadata.specific_info['BestGames-Rating'] = self.machine.bestgames_opinion
		self.metadata.specific_info['Version-Added'] = self.machine.version_added

		self.metadata.specific_info['Requires-Artwork'] = self.machine.requires_artwork
		self.metadata.specific_info['Is-Unofficial'] = self.machine.unofficial
		self.metadata.specific_info['Has-No-Sound-Hardware'] = self.machine.no_sound_hardware
		self.metadata.specific_info['Is-Incomplete'] = self.machine.incomplete
