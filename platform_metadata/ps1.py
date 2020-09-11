# from xml.etree import ElementTree

# from config.main_config import main_config
# from config.emulator_config import emulator_configs
#TODO: Resolve stupid annoying circular import so we can make this work

from .minor_systems import add_generic_info

# duckstation_config = emulator_configs.get('DuckStation')

# def add_duckstation_compat_info(metadata):
# 	compat_xml_path = duckstation_config.options.get('compatibility_xml_path')
# 	if not compat_xml_path:
# 		return

# 	try:
# 		compat_xml = ElementTree.parse(compat_xml_path)
# 		entry = compat_xml.find('entry[@code="{0}"]'.format(metadata.product_code))
# 		if entry is not None:
# 			compatibility = entry.attrib.get('compatibility')
# 			if compatibility:
# 				metadata.specific_config['DuckStation-Compatibility'] = compatibility

# 	except OSError as oserr:
# 		if main_config.debug:
# 			print('Oh dear we have an OSError trying to load compat_xml', oserr)
# 		return

def add_ps1_metadata(game):
	add_generic_info(game)
	# if game.metadata.product_code and duckstation_config:
	# 	add_duckstation_compat_info(game.metadata)
