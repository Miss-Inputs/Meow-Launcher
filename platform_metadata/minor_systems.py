#For mildly uninteresting systems that I still want to add system info for etc

from metadata import PlayerInput, InputType
from info.region_info import TVSystem

def add_entex_adventure_vision_info(game):
	game.metadata.tv_type = TVSystem.Agnostic
	player = PlayerInput()
	player.inputs = [InputType.Digital]
	player.buttons = 4 #Physically, they're on both sides of the system, but those are duplicates (for ambidextrousity)
	game.metadata.input_info.players.append(player)

def add_game_pocket_computer_info(game):
	game.metadata.tv_type = TVSystem.Agnostic
	player = PlayerInput()
	player.inputs = [InputType.Digital]
	player.buttons = 4
	game.metadata.input_info.players.append(player)

def add_gamate_info(game):
	game.metadata.tv_type = TVSystem.Agnostic
	player = PlayerInput()
	player.inputs = [InputType.Digital]
	player.buttons = 2
	game.metadata.input_info.players.append(player)
	game.metadata.input_info.console_buttons = 2
	

def add_mega_duck_info(game):
	game.metadata.tv_type = TVSystem.Agnostic
	player = PlayerInput()
	player.inputs = [InputType.Digital]
	player.buttons = 2
	game.metadata.input_info.players.append(player)
	game.metadata.input_info.console_buttons = 2
	
def add_watara_supervision_info(game):
	game.metadata.tv_type = TVSystem.Agnostic
	player = PlayerInput()
	player.inputs = [InputType.Digital]
	player.buttons = 2
	game.metadata.input_info.players.append(player)
	game.metadata.input_info.console_buttons = 2

def add_lynx_info(game):
	#TODO .lnx files should have a header with something in them, so eventually, Lynx will get its own module here
	game.metadata.tv_type = TVSystem.Agnostic
	player = PlayerInput()
	player.inputs = [InputType.Digital]
	player.buttons = 4 #Option 1, Option 2, A, B; these are flipped so you might think there's 8
	game.metadata.input_info.players.append(player)
	game.metadata.input_info.console_buttons = 1 #Pause
