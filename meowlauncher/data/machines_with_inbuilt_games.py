# Too many machines with inbuilt functionality that doesn't seem like a great idea to add
# BASIC: Acorn Electron, Amstrad CPC, Acorn Atom, Alice 32, SVI-3x8, ZX81, Videoton TVC etc
# Memory card management: PlayStation, Mega CD, Neo Geo CD, Saturn

# Warning messages
# BBC Bridge Companion
# Mattel HyperScan

# Non-game stuff that I guess I could put in here
# Acorn Archimedes: RISC OS 3.0.0, some apps
# Game Pocket Computer: Spirally test pattern
# Mattel Juice Box: Trailers
# Neo Geo Pocket: Calendar / horoscope
# V.Smile Baby: Learn and Discovery Home (whatever that does)
# Amiga / logica2: Logica Diagnostics #but which Amiga?

# Needs autoboot script:
# sms1 / bios13: Press Up + 1 + 2 to access Snail Maze
# RCA Studio 2: Bowling + Freeway + Patterns + Doodles + Math (this requires pressing F3 and then some number)

# Could really do with an autoboot script:
# Game.com: Solitaire + phone book + calculator + calendar
# VideoBrain: Text/colour/clock/alarm selectable by F1/F2/F3/F4
# V.Tech Socrates: Various maths/word games, "Super Paint"

# Buzztime Home Trivia System: Everything Trivia, but this is in the software list? Doesn't work anyway
# Vii, ekara could go in here if we need to make them systems to make their software list business work
# Gachinko Contest! Slot Machine TV: I dunno the game because it's written in kanji

from dataclasses import dataclass


@dataclass(frozen=True)
class InbuiltGame:
	name: str
	platform: str
	category: str


machines_with_inbuilt_games = {
	'apfm1000': InbuiltGame('Rocket Patrol', 'APF-MP1000', 'Games'),
	'astrocde': InbuiltGame('Gunfight + Checkmate + Calculator + Scribbling', 'Astrocade', 'Games'),
	'unichamp': InbuiltGame('Blackjack + Baccarat', 'Champion 2711', 'Games'),
	'channelf': InbuiltGame('Hockey + Tennis', 'Channel F', 'Games'),
	'dina': InbuiltGame(
		'Meteoric Shower', 'ColecoVision', 'Games'
	),  # Or should platform be "Dina" specifically…
	'gameking': InbuiltGame('Drifter + 2003 + Miner', 'GameKing', 'Games'),
	'gamekin3': InbuiltGame('Galaxy Crisis', 'GameKing 3', 'Games'),
	'vectrex': InbuiltGame('Mine Storm', 'Vectrex', 'Games'),
	'xegs': InbuiltGame('Missile Command', 'Atari 8-bit', 'Games'),
	'scv': InbuiltGame('Video Game Test Display', 'Super Cassette Vision', 'Tests'),
}

bioses_with_inbuilt_games = {
	('a7800', 'a7800pr'): InbuiltGame('Asteroids', 'Atari 7800', 'Games'),
	('sms', 'alexkidd'): InbuiltGame(
		'Alex Kidd in Miracle World', 'Master System', 'Games'
	),  # US/Europe
	('sms1', 'hangon'): InbuiltGame('Hang On', 'Master System', 'Games'),
	('sms1', 'hangonsh'): InbuiltGame(
		'Hang On + Safari Hunt', 'Master System', 'Games'
	),  # smsbr works for this too
	('sms1', 'missiled'): InbuiltGame('Missile Defense 3D', 'Master System', 'Games'),  # US/Europe
	('smspal', 'sonic'): InbuiltGame(
		'Sonic the Hedgehog', 'Master System', 'Games'
	),  # Europe/Brazil
}
