#!/usr/bin/env python3

from collections.abc import Iterable, Sequence
from typing import Optional

from meowlauncher.common_types import EmulationStatus
from meowlauncher.config.emulator_config import emulator_configs
from meowlauncher.config.main_config import main_config
from meowlauncher.config.platform_config import (PlatformConfig,
                                                 platform_configs)
from meowlauncher.data.machines_with_inbuilt_games import (
    InbuiltGame, bioses_with_inbuilt_games, machines_with_inbuilt_games)
from meowlauncher.game_source import GameSource
from meowlauncher.games.mame.mame import ConfiguredMAME
from meowlauncher.games.mame.mame_game import MAMEGame, MAMELauncher
from meowlauncher.games.mame.mame_inbuilt_game import (MAMEInbuiltGame,
                                                       MAMEInbuiltLauncher)
from meowlauncher.games.mame.mame_metadata import add_metadata, add_status
from meowlauncher.games.mame_common.machine import (
    Machine, get_machine, iter_machines_from_source_file, iter_machines)
from meowlauncher.games.mame_common.mame_helpers import (
    default_mame_executable, have_mame)
from meowlauncher.util.desktop_files import has_been_done


def _is_actually_machine(machine: Machine) -> bool:
	if machine.xml.attrib.get('isbios', 'no') == 'yes': #Hmm, technically there's nothing stopping you launching these
		return False

	if main_config.exclude_system_drivers and machine.is_system_driver:
		return False

	return True

class MAME(GameSource):
	def __init__(self, driver_list: Sequence[str]=None, source_file: str=None) -> None:
		super().__init__()
		self.driver_list = driver_list
		self.source_file = source_file
		self.emu = ConfiguredMAME(emulator_configs.get('MAME'))
		self.platform_config = PlatformConfig('MAME', set(), (), {}) #Not needed for now, it is just to satisfy EmulatedGame constructor… may be a good idea some day

	@property
	def name(self) -> str:
		return 'MAME'

	@property
	def description(self) -> str:
		return 'MAME machines'

	@property
	def is_available(self) -> bool:
		return have_mame()

	def no_longer_exists(self, game_id: str) -> bool:
		#TODO: Put is_available in ConfiguredEmulator and then you can check that as well
		return default_mame_executable.verifyroms(game_id)

	def _process_machine(self, machine: Machine) -> Optional[MAMELauncher]:
		if machine.source_file in main_config.skipped_source_files:
			return None

		if not _is_actually_machine(machine):
			return None

		if not machine.launchable:
			return None

		if main_config.exclude_non_working and machine.emulation_status == EmulationStatus.Broken and machine.basename not in main_config.non_working_whitelist:
			#This will need to be refactored if anything other than MAME is added
			#The code behind -listxml is of the opinion that protection = imperfect should result in a system being considered entirely broken, but I'm not so sure if that works out
			return None

		if machine.is_probably_skeleton_driver:
			#Well, we can't exactly play it if there's no controls to play it with (and these will have zero controls at all);
			#this basically happens with super-skeleton drivers that wouldn't do anything even if there was controls wired up
			return None

		game = MAMEGame(machine, self.platform_config)
		if not game.is_wanted:
			return None

		if not self.emu.executable.verifyroms(machine.basename):
			#We do this as late as we can after checks to see if we want to actually add this machine or not, because it takes a while (in a loop of tens of thousands of machines), and hence if we can get out of having to do it we should
			#However this is a reminder to myself to stop trying to be clever (because I am not); we cannot assume -verifyroms would succeed if machine.romless is true because there might be a device which is not romless
			return None

		add_metadata(game)
		
		return MAMELauncher(game, self.emu)

	def iter_launchers(self) -> Iterable[MAMELauncher]:
		if self.driver_list:
			for driver_name in self.driver_list:
				launcher = self._process_machine(get_machine(driver_name, default_mame_executable))
				if launcher:
					yield launcher
			return 

		if self.source_file:		
			for machine in iter_machines_from_source_file(self.source_file, self.emu.executable):
				if not _is_actually_machine(machine):
					continue
				if not machine.launchable:
					continue
				if not self.emu.executable.verifyroms(machine.basename):
					continue
				launcher = self._process_machine(machine)
				if launcher:
					yield launcher
			return

		for machine in iter_machines(self.emu.executable):
			if not main_config.full_rescan:
				if has_been_done('Arcade', machine.basename):
					continue
				if has_been_done('MAME', machine.basename):
					continue

			launcher = self._process_machine(machine)
			if launcher:
				yield launcher

class MAMEInbuiltGames(GameSource):
	def __init__(self) -> None:
		super().__init__()
		self.blank_platform_config = PlatformConfig('MAME', set(), (), {})

	@property
	def name(self) -> str:
		return 'MAME inbuilt games'

	@property
	def description(self) -> str:
		return 'MAME inbuilt games'

	@property
	def is_available(self) -> bool:
		return have_mame()

	def no_longer_exists(self, game_id: str) -> bool:
		return not default_mame_executable or not default_mame_executable.verifyroms(game_id.split(':')[0])

	def _process_inbuilt_game(self, machine_name: str, inbuilt_game: InbuiltGame, bios_name=None) -> Optional[MAMEInbuiltLauncher]:
		if not default_mame_executable.verifyroms(machine_name):
			return None

		#Actually, this probably doesn't matter at all… but eh, just feels more correct than simply passing blank_platform_config to satisfy EmulatedGame constructor
		platform_config = platform_configs.get(inbuilt_game.platform, self.blank_platform_config)
			
		#MachineNotFoundException shouldn't happen because verifyroms already returned true? Probably
		machine = get_machine(machine_name, default_mame_executable)
		
		game = MAMEInbuiltGame(machine_name, inbuilt_game, platform_config, bios_name)
		add_status(machine, game.metadata)
		return MAMEInbuiltLauncher(game, ConfiguredMAME(emulator_configs.get('MAME')))

	def iter_launchers(self) -> Iterable[MAMEInbuiltLauncher]:
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
