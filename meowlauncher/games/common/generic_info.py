from typing import TYPE_CHECKING

from meowlauncher.util.region_info import TVSystem

if TYPE_CHECKING:
	from meowlauncher.games.mame_common.software_list import Software
	from meowlauncher.metadata import Metadata
	
def add_generic_software_info(software: 'Software', metadata: 'Metadata'):
	software.add_standard_metadata(metadata)
	metadata.add_notes(software.get_info('usage'))
	if 'pcb' in software.infos:
		metadata.specific_info['PCB'] = software.get_info('pcb')
	metadata.specific_info['Requirement'] = software.get_shared_feature('requirement')
	try:
		metadata.specific_info['TV Type'] = TVSystem(software.get_info('video'))
	except ValueError:
		pass
	for info_name, info_value in software.infos.items():
		if info_name in {'usage', 'release', 'serial', 'developer', 'alt_title', 'alt_name', 'alt_disk', 'barcode', 'ring_code', 'version', 'video', 'pcb'}:
			#We have already added this
			continue
		metadata.specific_info[info_name.replace('_', '-').replace(' ', '-').title()] = info_value