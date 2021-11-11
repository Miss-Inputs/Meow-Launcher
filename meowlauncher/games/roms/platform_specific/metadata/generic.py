from meowlauncher.games.mame.software_list_info import get_software_list_entry
from meowlauncher.games.roms.rom_game import ROMGame
from meowlauncher.util.region_info import TVSystem

def add_generic_info(game: ROMGame):
	#For any system not otherwise specified
	if game.rom.is_folder:
		return
	software = get_software_list_entry(game)

	if software:
		software.add_standard_metadata(game.metadata)
		game.metadata.add_notes(software.get_info('usage'))
		if 'pcb' in software.infos:
			game.metadata.specific_info['PCB'] = software.get_info('pcb')
		game.metadata.specific_info['Requirement'] = software.get_shared_feature('requirement')
		try:
			game.metadata.specific_info['TV-Type'] = TVSystem(software.get_info('video'))
		except ValueError:
			pass
		for info_name, info_value in software.infos.items():
			if info_name in ('usage', 'release', 'serial', 'developer', 'alt_title', 'alt_name', 'alt_disk', 'barcode', 'ring_code', 'version', 'video', 'pcb'):
				#We have already added this
				continue
			game.metadata.specific_info[info_name.replace('_', '-').replace(' ', '-').title()] = info_value
