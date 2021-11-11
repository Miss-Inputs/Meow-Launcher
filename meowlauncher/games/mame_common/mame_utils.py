from typing import Optional

from meowlauncher.data.name_cleanup.mame_manufacturer_name_cleanup import (
    dont_remove_suffix, manufacturer_name_cleanup)
from meowlauncher.util.utils import junk_suffixes

def consistentify_manufacturer(manufacturer: Optional[str]) -> Optional[str]:
	if not manufacturer:
		return None
	if manufacturer not in dont_remove_suffix:
		while junk_suffixes.search(manufacturer):
			manufacturer = junk_suffixes.sub('', manufacturer)
	manufacturer = manufacturer.strip()
	if manufacturer[-1] == '?':
		return manufacturer_name_cleanup.get(manufacturer[:-1], manufacturer[:-1]) + '?'
	return manufacturer_name_cleanup.get(manufacturer, manufacturer)

image_config_keys = {
	'Cabinet': 'cabinets_directory',
	'Control Panel': 'cpanels_directory',
	'PCB': 'pcbs_directory',
	'Flyer': 'flyers_directory',
	'Title Screen': 'titles_directory',
	'End Screen': 'ends_directory',
	'Marquee': 'marquees_directory',
	'Artwork Preview': 'artwork_preview_directory',
	'Boss Screen': 'bosses_directory',
	'Logo Screen': 'logos_directory',
	'Score Screen': 'scores_directory',
	'Versus Screen': 'versus_directory',
	'Game Over Screen': 'gameover_directory',
	'How To Screen': 'howto_directory',
	'Select Screen': 'select_directory',
	'Icon': 'icons_directory',
	'Cover': 'covers_directory', #Software only
}
