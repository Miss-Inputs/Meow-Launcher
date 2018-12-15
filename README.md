# Meow Launcher

Utility to create launchers for games.

This readme may evolve as time goes on. It probably sucks because all single-person projects inherently will have a problem with documentation as a developer's perspective of their own software is going to be different from a hypothetical person who doesn't know its ins and outs, but also I just suck at writing. So, no need to be afraid to ask questions.

Eventually it started out when one day I was indecisive about what game to play, and I decided to make a little single-file script to assist me in the "I feel like playing a video game" process, and then I got carried away and took things too far and I ended up doing all this.

So what makes this different:
- Uses the emulators that you already have installed (or are going to install), rather than installing its own version which may be out of date or have altered compatibility
- You can use whatever frontend you want on top of this: This just generates launchers, and you can decide how you want to use them, instead of being locked down to some giant frontend which combines all the things and doesn't let you mix and match functionality.
- Code is organized, hopefully, in such a way that it should be relatively easy to add your own emulators if you have some new one that I didn't think about; or tweak some other tweak that might be interesting

It's not intended to be hard to use, it just hasn't been made easier to use yet. One day it should be.

The other neat tricks are that it will automatically get metadata from the games where it can, not using any weird internet service that may disappear or have restrictions on usage, but from what's inside the games themselves. Also it will automatically figure out which emulator (where emulation is applicable) is the best one to use for a given game, out of the emulators you selected.

No special trickery should be required for installation, you just kinda put it in whichever folder you feel like putting it in. Shouldn't really require external libraries, but you can look at requirements.txt for optional stuff, or I'll tell you that here:
- Pillow: For extracting embedded icons from things (DS, 3DS, etc)
- steamfiles: Required to add Steam games
- hfsutils: For Mac games to work, will need to be in the path somewhere. Sorry

These config files will appear in ~/.config/MeowLauncher (see also config.py config_dir for where that's set) with default values, once anything is ran for the first time (see --refresh-config below), and then you... edit them. Ideally I want to make some kind of configurator, but that'd be a separate thing:
- config.ini
  - Main configuration, which specifies where your launchers are output to and other things like that.
- emulators.ini
  - For roms.py, dos.py and mac.py; this is where you specify where your games are located and which emulators you want to use. You can use multiple ROM directories and multiple emulators; with the latter, it'll use the emulator you specified first, and if that emulator won't work with a given game, it'll try the next emulator, etc.
- ignored_directories.txt
  - List of directories to ignore despite them being inside your ROM folders. Sometimes you just have subfolders that you don't want having launchers for. One directory per line. This doesn't appear by default, but you can just create it.
- dos.ini, mac.ini
  - These are automatically generated by the respective modules, but you might need to edit them.

There's also name_consistency.ini which I've for some reason decided to put in the source directory here. It makes names consistent.

DOS and Mac games will require [https://github.com/Zowayix/computer-software-db](ComputerSoftwareDB), or you could look at how the database format works there, and make your own.

Once you have everything set up, just run main.py to output all the launchers to the designated output folder. It takes a while. Oh well.  
Command line arguments:  
- --refresh-config
  - Does nothing except load the config and then exit: This has the effect that if there's config values or new emulated systems that aren't in your configuration files, this will automatically add blank/default entries for them, rather than you having to type things in yourself. I guess that's how I'll deal with me adding new things, until I think of something better.
- --debug
  - Displays a lot of console spam. I should probably make this more specific with different command line arguments for what kind of console spam. But I haven't. Mostly it'll just tell you "there's something weird about this ROM, or it's not able to be emulated yet", and that sort of thing.
- --super-debug
  - This is for even more console spam when regular --debug isn't enough. It's basically used for disambiguate.py to tell you every single launcher that gets disambiguated.
- --print-times
  - Prints how long stuff takes.
- --regen-dos-config
  - Regenerates DOSBox config files for DOS games. Normally it just uses what's already there (allowing you to tweak them for your own evil purposes).
- --no-arcade
  - Skips mame_machines.py. It takes a while, but then so does roms.py these days, so... should I have this here? Hmm
- --organize-folders
  - Activates the in-built thing where it organizes your launchers into folders.
	- --extra-folders
	  - Even more folders for metadata that probably nobody cares about.

Sources of games:  
- roms.py
  - This is probably what most people are interested in: Just normal ROMs to be used with an emulator. For every kind of platform possible, I don't just include the platforms that are "popular". If it can be emulated, it can have a launcher generated.
  - Also contains games with source ports or engines, like Doom and whatnot.
  - To use with individual systems, use the --systems argument and then a comma-separated list of system names, e.g. --systems GBA,N64
  - To use with a single ROM, use the --rom argument with a path and then a system name, e.g.: --rom /path/blah.tap C64 (this will probably not be too useful except for debugging/development/etc)
- mame_machines.py
  - For arcade romsets, except they aren't always arcade machines anyway, this will also include handheld systems and plug & play consoles and all of that sort of thing. It only creates launchers for romsets you actually have, of course. None of that crap where it lists "unavailable" machines, because that doesn't really make sense.
- scummvm.py
  - Games that are "emulated" (is that really the right word?) via ScummVM. You'd need to configure them and put them in your ScummVM library first.
- dos.py
  - DOS executables, not floppy disks or stuff like that yet. They're intended to be used with something like DOSBox, where you have a folder that pretends to be a hard drive on a DOS machine.
  - Creates DOSBox configuration files for each game (if you're using DOSBox, which you would be unless you tweaked the code yourself).
  - Requires you to run this module with the --scan argument first in order to figure out what games you actually have.
- mac.py
  - Mac software, stored in a hard disk image (because that's how you would generally want to do this). 
  - This is the part that sucks the most, because right now you need a script inside the Mac boot disk to read from the shared folder (so you need an emulator that supports that too) and automatically boot stuff...
  - Also requires you to run this module with the --scan argument.
- steam.py
  - Steam games (running natively on Linux/with Steam Play), if you have it installed.
  - Not the non-Steam game shortcuts, it'd be asking for trouble.

Other places of interest:  
- disambiguate.py
  - In the likely event that there are multiple games with the same name (or more commonly more than one version of a game), this will add stuff in brackets to enable you to know which one is which.
- organize_folders.py
  - This is like a builtin mini-frontend. After dealing with all your launchers, it copies them all into lots of subfolders, and you can browse them that way.

And then you can take those .desktop files and do what you want. Put them in your applications menu, put them into Steam, that's your own business, and I won't force any particular thing on you.

In future I want to make a GUI frontend myself but I haven't yet.

(See third-party-copyright-stuff.txt for third party stuff used)

Use [this](https://gist.github.com/Zowayix/f511490865bc5aa8a66ad0776ae066df) to regenerate nintendo_licensee_codes from ROMniscience's source if you need to (adjusting the local path to the source file accordingly). Not that anyone would probably want this project if I got hit by a bus, but maybe someone wants to know how to do that. I'm not cool enough to have any sort of automated build steps or whatever.

That's all for this readme, keep on meowing gamers
