__doc__ = """Putting Steam-related enums here"""


from enum import IntFlag, IntEnum


class StateFlags(IntFlag):
	"""See also https://github.com/SteamDatabase/SteamTracking/blob/master/Structs/EAppState.h
	Used in .acf manifests"""
	Invalid = 0
	Uninstalled = 1
	UpdateRequired = 2
	FullyInstalled = 4
	UpdateQueued = 8
	UpdateOptional = 16
	FilesMissing = 32
	SharedOnly = 64
	FilesCorrupt = 128
	UpdateRunning = 256
	UpdatePaused = 512
	UpdateStarted = 1024
	Uninstalling = 2048
	BackupRunning = 4096
	AppRunning = 8192
	ComponentInUse = 16384
	MovingFolder = 32768
	Reconfiguring = 65536
	PrefetchingInfo = 131072

class ExternalAccountType(IntEnum):
	"""https://github.com/SteamDatabase/SteamTracking/blob/master/Structs/enums.steamd#L916 (EExternalAccountType)"""
	None_ = 0
	Steam = 1
	Google = 2
	Facebook = 3
	Twitter = 4
	Twitch = 5
	YouTube = 6
	FacebookPage = 7
