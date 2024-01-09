#!/usr/bin/env python3

from collections.abc import Iterator

from meowlauncher.config import main_config
from meowlauncher.settings.emulator_config import emulator_configs
from meowlauncher.settings.platform_config import platform_configs
from meowlauncher.config_types import PlatformConfig
from meowlauncher.data.machines_with_inbuilt_games import (
	InbuiltGame,
	bioses_with_inbuilt_games,
	machines_with_inbuilt_games,
)
from meowlauncher.game_source import GameSource
from meowlauncher.games.mame.mame import ConfiguredMAME
from meowlauncher.games.mame.mame_config import ArcadeMAMEConfig
from meowlauncher.games.mame.mame_game import MAMEGame, MAMELauncher
from meowlauncher.games.mame.mame_inbuilt_game import MAMEInbuiltGame, MAMEInbuiltLauncher
from meowlauncher.games.mame.mame_info import add_info, add_status
from meowlauncher.games.mame_common.machine import (
	Machine,
	MAMEStatus,
	get_machine,
	iter_machines,
	iter_machines_from_source_file,
)
from meowlauncher.games.mame_common.mame_executable import MAMENotInstalledException
from meowlauncher.util.desktop_files import has_been_done


class Arcade(GameSource):
	"""Arcade machines, and also plug & play games and handhelds and other things that aren't arcade machines but would also logically go here as they are launchable by MAME (nitpicking is not allwoed)"""
	def __init__(self) -> None:
		super().__init__()
		self.config: ArcadeMAMEConfig
		self.emu: ConfiguredMAME | None = None
		try:
			mame_config = emulator_configs.get('MAME')
			if mame_config:
				self.emu = ConfiguredMAME(mame_config)
		except MAMENotInstalledException:
			pass
		self.platform_config = PlatformConfig('MAME', set(), (), {}) #TODO: Refactor EmulatedGame constructor so we don't do this

	@classmethod
	def description(cls) -> str:
		return 'Arcade / standalone machines'

	@classmethod
	def config_class(cls) -> type[ArcadeMAMEConfig] | None:
		return ArcadeMAMEConfig

	@property
	def is_available(self) -> bool:
		return self.emu is not None

	def no_longer_exists(self, game_id: str) -> bool:
		if not self.emu:
			return True
		return not self.emu.executable.verifyroms(game_id)

	def _process_machine(self, machine: Machine) -> MAMELauncher | None:
		"""Returns a launcher for this machine, or none if it can't/shouldn't/etc"""
		assert self.emu, 'Arcade._process_machine should never be called without checking is_available! What the'
		if machine.source_file in self.config.skipped_source_files:
			return None

		if machine.is_bios: #Hmm, technically there's nothing stopping you launching these, but generally nobody wants this
			return None

		if self.config.exclude_system_drivers and machine.is_system_driver:
			return None

		if not machine.launchable:
			return None

		if self.config.exclude_non_working and machine.emulation_status == MAMEStatus.Preliminary and machine.basename not in self.config.non_working_whitelist:
			#This will need to be refactored if anything other than MAME is added
			#The code behind -listxml is of the opinion that protection = imperfect should result in a system being considered entirely broken, but I'm not so sure if that works out
			return None

		if machine.is_probably_skeleton_driver:
			#Well, we can't exactly play it if there's no controls to play it with (and these will have zero controls at all);
			#this basically happens with super-skeleton drivers that wouldn't do anything even if there was controls wired up
			return None

		game = MAMEGame(machine, self.platform_config, self.config)
		if not game.is_wanted:
			return None

		if not self.emu.executable.verifyroms(machine.basename):
			#We do this as late as we can after checks to see if we want to actually add this machine or not, because it takes a while (in a loop of tens of thousands of machines), and hence if we can get out of having to do it we should
			#However this is a reminder to myself to stop trying to be clever (because I am not); we cannot assume -verifyroms would succeed if machine.romless is true because there might be a device which is not romless
			return None

		add_info(game)
		
		return MAMELauncher(game, self.emu)

	def iter_launchers(self) -> Iterator[MAMELauncher]:
		assert self.emu, 'Arcade.iter_launchers should never be called without checking is_available! What the'
		if self.config.drivers:
			for driver_name in self.config.drivers:
				launcher = self._process_machine(get_machine(driver_name, self.emu.executable))
				if launcher:
					yield launcher
			return 

		for machine in iter_machines_from_source_file(self.config.source_files, self.emu.executable) if self.config.source_files else iter_machines(self.emu.executable):
			if not main_config.full_rescan:
				if has_been_done('Arcade / standalone machines', machine.basename):
					continue

			launcher = self._process_machine(machine)
			if launcher:
				yield launcher

	@classmethod
	def game_type(cls) -> str:
		return 'Arcade / standalone machines'

class MAMEInbuiltGames(GameSource):
	"""MAME machines that are consoles, etc that have games inbuilt into them which wouldn't be used with just ROMs"""

	def __init__(self) -> None:
		super().__init__()
		self.blank_platform_config = PlatformConfig('MAME', set(), (), {})
		self.emu: ConfiguredMAME | None = None
		try:
			mame_config = emulator_configs.get('MAME')
			if mame_config:
				self.emu = ConfiguredMAME(mame_config)
		except MAMENotInstalledException:
			pass

	@classmethod
	def name(cls) -> str:
		return 'MAME inbuilt games'

	@classmethod
	def description(cls) -> str:
		return 'MAME inbuilt games'

	@classmethod
	def game_type(cls) -> str:
		return 'Inbuilt game'

	@property
	def is_available(self) -> bool:
		return self.emu is not None

	def no_longer_exists(self, game_id: str) -> bool:
		return not self.emu or not self.emu.executable.verifyroms(game_id.split(':')[0])

	def _process_inbuilt_game(self, machine_name: str, inbuilt_game: InbuiltGame, bios_name: str | None=None) -> MAMEInbuiltLauncher | None:
		assert self.emu, 'MAMEInbuiltGames._process_inbuilt_game should never be called without checking is_available! What the'
		if not self.emu.executable.verifyroms(machine_name):
			return None

		#Actually, this probably doesn't matter at all… but eh, just feels more correct than simply passing blank_platform_config to satisfy EmulatedGame constructor
		platform_config = platform_configs.get(inbuilt_game.platform, self.blank_platform_config)
			
		#MachineNotFoundException shouldn't happen because verifyroms already returned true? Probably
		machine = get_machine(machine_name, self.emu.executable)
		
		game = MAMEInbuiltGame(machine_name, inbuilt_game, platform_config, bios_name)
		add_status(machine, game.info)
		return MAMEInbuiltLauncher(game, self.emu)

	def iter_launchers(self) -> Iterator[MAMEInbuiltLauncher]:
		for machine_name, inbuilt_game in machines_with_inbuilt_games.items():
			if not main_config.full_rescan:
				if has_been_done('Inbuilt game', machine_name):
					continue
			launcher = self._process_inbuilt_game(machine_name, inbuilt_game)
			if launcher:
				yield launcher
		for machine_and_bios_name, inbuilt_game in bioses_with_inbuilt_games.items():
			if not main_config.full_rescan:
				if has_been_done('Inbuilt game', machine_and_bios_name[0] + ':' + machine_and_bios_name[1]):
					continue
			launcher = self._process_inbuilt_game(machine_and_bios_name[0], inbuilt_game, machine_and_bios_name[1])
			if launcher:
				yield launcher	
