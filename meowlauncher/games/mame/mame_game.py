from typing import TYPE_CHECKING

from meowlauncher.emulator_launcher import EmulatorLauncher
from meowlauncher.game import Game
from meowlauncher.info import Date

if TYPE_CHECKING:
	from meowlauncher.games.mame_common.machine import Machine
	from meowlauncher.games.mame_common.mame import MAME

	from .mame_config import ArcadeMAMEConfig


class ArcadeGame(Game):
	"""Wrapper around Machine to add info fields and stuff I guess
	Hmm… the class design here is probably not that good, but eh, it works I guess"""

	def __init__(self, machine: 'Machine', config: 'ArcadeMAMEConfig'):
		super().__init__()
		self.machine = machine
		self.config = config

		self._add_metadata_fields()

	@property
	def name(self) -> str:
		return self.machine.name

	def _add_metadata_fields(self) -> None:
		self._has_inited_metadata = True
		self.info.specific_info['Source File'] = self.machine.source_file
		self.info.specific_info['Family'] = self.machine.family
		if self.machine.has_parent:
			self.info.specific_info['Has Parent?'] = True

		self.info.release_date = Date(self.machine.xml.findtext('year'))

		self.info.specific_info['Number of Players'] = self.machine.number_of_players
		if self.machine.is_mechanical:
			self.info.specific_info['Is Mechanical?'] = True
		if self.machine.uses_device('ticket_dispenser'):
			self.info.specific_info['Dispenses Tickets?'] = True
		self.info.specific_info['Coin Slots'] = self.machine.coin_slots
		if self.machine.requires_chds:
			self.info.specific_info['Requires CHD?'] = True
		if self.machine.romless:
			self.info.specific_info['Romless'] = True
		self.info.specific_info['Slot Names'] = {
			next(iter(slot.instances))[0] for slot in self.machine.media_slots if slot.instances
		}  # I guess I only expect one?
		self.info.specific_info['Software Lists'] = self.machine.software_list_names
		self.info.series = self.machine.series
		bios = self.machine.bios
		if bios:
			self.info.specific_info['BIOS Used'] = bios
		if self.machine.samples_used:
			self.info.specific_info['Samples Used'] = self.machine.samples_used
		arcade_system = self.machine.arcade_system
		if arcade_system:
			self.info.specific_info['Arcade System'] = arcade_system

		licensed_from = self.machine.licensed_from
		if self.machine.licensed_from:
			self.info.specific_info['Licensed From'] = licensed_from

		hacked_by = self.machine.hacked_by
		if self.machine.hacked_by:
			self.info.specific_info['Hacked By'] = hacked_by

		self.info.developer, self.info.publisher = self.machine.developer_and_publisher

		self.info.specific_info['BestGames Rating'] = self.machine.bestgames_opinion
		self.info.specific_info['Version Added'] = self.machine.version_added

		if self.machine.requires_artwork:
			self.info.specific_info['Requires Artwork?'] = True
		if self.machine.unofficial:
			self.info.specific_info['Is Unofficial?'] = True
		if self.machine.no_sound_hardware:
			self.info.specific_info['Has No Sound Hardware?'] = True
		if self.machine.incomplete:
			self.info.specific_info['Is Incomplete?'] = True

	@property
	def is_wanted(self) -> bool:
		if self.config.exclude_pinball and self.machine.is_pinball:
			return False
		if self.config.exclude_non_arcade and self.info.platform == 'Non-Arcade':
			return False

		return True


class MAMELauncher(EmulatorLauncher):
	def __init__(self, game: ArcadeGame, emulator: 'MAME') -> None:
		self.game: ArcadeGame = game
		super().__init__(game, emulator)

	@property
	def game_id(self) -> str:
		return self.game.machine.basename
