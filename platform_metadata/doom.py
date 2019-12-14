from common_types import SaveType

def add_doom_metadata(game):
	magic = game.rom.read(amount=4)
	if magic == b'PWAD':
		game.metadata.specific_info['Is-PWAD'] = True
	
	game.metadata.save_type = SaveType.Internal
	