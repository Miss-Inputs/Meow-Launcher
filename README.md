# Meow Launcher

<img alt="Meow Launcher's logo" src="gui/icon.png?raw=true" width="300" />

This is just a general warning that overrides anything else I say in this readme, for the time being. Right now this project is in a state where it only really makes sense for me to use it, it's just not ready for general purpose use yet. Not configurable enough. It did just evolve from a little script I made one day and I took things too far, after all; anyway it is here in the hope that one day it will be useful to others, and I guess you could look at it if there's something there useful to you, but like probably not because you could probably just use any one of the other "automatically generate the right command lines to launch an emulator" tools out there, and I didn't because I didn't like them and so I made one for my own weird purposes.

Actually I'm not sure why I'm bothering to leave the rest of this readme intact anyway, since by the time I remove that warning, it'll all be out of date. I'm sure some of that is out of date already.

Truth be told this is like,,, it's not that this project is abandoned, far from it because I stare into the VS Code window every day, but right now I'm not really in a place in real life where I can focus or be that productive. I guess you could call it a hiatus of sorts, if you wanted to call it something.

--- end warning

So, Meow Launcher aims to take away the hassle of going through games and actually launching them. It automatically supplies the right command line options to things so they work properly, basically aims to create a "console-like" experience for as many games as possible, i.e. you say "I am going to play this game" and then you launch the game and then you can play the game, without having to think too much.

Eventually it started out when one day I was indecisive about what game to play, and I decided to make a little single-file script to assist me in the "I feel like playing a video game" process, and then I got carried away and took things too far and I ended up doing all this.

Meow Launcher aims to do one thing well instead of combining everything into a single thing, so it will just create desktop shortcut files to automatically launch the games. I intend to one day make some other things to go along with it, but I haven't yet. Hence, it does not do these things that other frontends might do:  

- Installing the emulators; Meow Launcher is designed instead to use what's already there, rather than having its own version which might be a fork which isn't kept to date with upstream, or just outdated, or unavailable
- Configuring the emulators (directories and controllers etc)
- Browsing what games you have with a nice little GUI and a library and whatnot; this is the most significant part to keep separated I guess. This is the next thing I want to do eventually, and hopefully when I do that it'll all make more sense.

I hope one day I can get around to writing all this other stuff which allows for a nice complete easy to use experience while still being modular.

The other main thing is that it looks inside ROM headers etc for metadata, in order to 1) automatically use the right command line options for certain things, or select which emulator is the best choice by determining what's incompatible, and that sort of thing and 2) help you organize your games and decide on what to play (this will become more useful once I make the game browser) 3) I want to and it's fun.

For now, you just use your file manager to browse your games and launch them (or any other app you have that launches .desktop files, which of course file managers are meant to do; you could put them all in your application menu if you wanted).

Other things I will not be doing:  
- Relying on databases of games, and only "scraping" games that exist in that database. I hope I don't have to explain why that's silly! I will let you be a hipster and play games I've never heard of, or hacks or translations or homebrew that tends to not be in those databases, or stuff you create yourself, etc.  
- Relying on online services to get metadata, and I swear it's not just because I'm too socially awkward to register with any of them, I just don't like overcomplicating things like that.  

So, as part of my mission to create that "console-like" experience, I sorta curate emulators and emulated platforms to what I can get that experience with. Nothing that requires manually typing in weird commands that I'll probably forget, automatically boot the thing or get outta here, kid. Of course, if I can make the emulator programmatically type the command or select the thing from the menu myself, well, that sounds fun and I will definitely do that. Otherwise, it's like… why bother having a frontend if I have to do the booting stuff part myself?

Anyway! That was a lot of words for me to just try and explain what it does. So, this is the part where I say that Meow Launcher is like... super-alpha right now. It doesn't even have a version number yet - I'm just changing around things as I see fit until I'm comfy.

Basically it needs testing from other people. I use it daily when I feel like playing stuff, and I can say that it works enough for me, but if I were to say "yeah it works for me so it should work for everyone else" that'd be really stupid, wouldn't it? I encourage others to try it out if they have the patience to test experimental stuff (and they're interested in what it aims to do), but I imagine it would have several problems, probably among the lines of "my code expects this to exist in this place but it doesn't always exist there" and it breaks horribly. Maybe! I don't know. To my knowledge, nobody else has actually used it yet.

Anyway, don't be afraid to say "this is what I would like for Meow Launcher to be nice and useable for me", or something like that. Worst case scenario is that I will say "nah that's not what I wanna do" and then I don't do it, because it's a hobby project and I do what I want; but I do want to make something that helps people (that's why I'm here putting stuff on GitHub) and if I can make it work for you, then hey that's pretty cool.

Things that I know are a bit flaky right now, and why I don't wanna do v0.1 just yet:

- Installation of Meow Launcher itself. Just kinda download it and put it in a folder? I haven't grokked exactly what to do with setuptools or whatsitcalled.
- The GUI. The bloody GUI! I actually forgot I was gonna make one until I looked at the milestone for v0.1 and it was like… oh yeah, that thing. I did try and put one together, but the thing is, I'm just not a designer, really. I have to admit GUI design is not my strong suit. So that's sitting there incomplete. I do think that would be important, though, unless maybe it turns out nobody really cares and just uses the command line (like I do) and then I don't bother.
- DOS games currently require an [https://github.com/Zowayix/computer-software-db](external database) that I made, which goes against exactly my principle of not requiring external databases. I want to throw it all out and start over, well not quite, but the code and design there is a load of crap. I want people to be able to specify their own games and specify the metadata/config themselves, and then the database is just there as a "hey that .exe could be this game, if you want I can provide metadata and config that I know for you"; as I understand it that's how other DOSBox frontends work. I also want to support floppy and CD images but that's another story.
- Mac games are just like… bleh. To scan things from your drive images, which I haven't implemented yet anyway, you need [https://pypi.org/project/machfs/](machfs). The second thing is that you need a [https://gist.github.com/Zowayix/8bde015b7265d72bffdf8363331cf04a](very dodgy AppleScript) to go inside the Startup Items of the guest OS (if you want to actually autoboot the software), and that's kinda nasty, so I'll have to have a think about what to do there. I guess it's unavoidable for now…
- Configuring Meow Launcher the first time is a bit awkward: since the configuration file doesn't exist yet, it doesn't know where your games are stored, and so I guess you would have to run a thing that says "hey just generate the configuration files" and then you edit them and then run it normally (I did try and do that but that doesn't work at the moment because I'm an idiot), or I'd have to make a Meow Launcher config utility which you use first (well, the GUI would be this, but then I didn't get around to finishing it).
- Currently sorta assumes you have one version of MAME, and it's a recent enough version that it supports the drivers and options I expect, etc. (well, it shouldn't break right now if you don't have it installed entirely)
- Emulators gotta be in the path, it doesn't yet let you say "this emulator is located over here, go launch it from there"

Windows (as in running Meow Launcher on Windows, not necessarily emulating Windows) is kinda planned at some point in the distant future. I just don't have a Windows setup at the moment so it'd be a bit awkward to develop, but as long as there's still emulators that are on Windows and haven't been ported, or game launchers exclusive to Windows (looking at you uPlay because I have games on there), I'm gonna want to make a Windows version.

The other things that you should know is that Pillow is required to extract icons and other images from ROMs that have those embedded (DS, 3DS, etc); and steamfiles is required for Steam games to work. That's all in requirements.txt anyway.

So, what games does Meow Launcher launch, anyway? Should I have put this part somewhere up there? Maybe!

- MAME machines (arcade games, but also plug & play games or Game & Watch or what have you), what you actually have and none of that "unavailable" business
- ROMs to be launched by an emulator
- Games with source ports (Doom, Quake); these are treated like pseudo-ROMs
- Aforementioned DOS and Mac that are a bit weird right now
- ScummVM (whatever you have added to your ScummVM config already)
- Steam, if you have that installed; not non-Steam game shortcuts because that would get weird

In progress is MAME software but I haven't done that yet.

TODO: Describe the config files in more detail and also dos.json/mac.json is wrong:

- config.ini: General configuration
- systems.ini: For ROMs, specifies where you put them, and also what emulators you want to use
- ignored_directories.txt: Skip over these directories (one per line) (config.py also does this sort of thing, so maybe I should put that into there)
- dos.ini, mac.ini: These are generated by ./dos.py --scan and ./mac.py --scan, but I did say I was gonna redo that whole business, so never mind really.

TODO: Describe the command line arguments that are actually important, but for now, I'll mention these:

- --full-rescan: Normally Meow Launcher leaves your existing launchers alone (unless they refer to games that aren't there anymore), and only adds launchers for what isn't there since last time; this just avoids all that and throws the whole output folder out and starts again anew
- --debug prints some verbose stuff that you might not care about (but it includes things like "I won't launch this game because it won't work for whatever reason" so that might come in handy)
- --print-times prints how long everything takes, which is also something you might not care about
- --organize-folders sorts your games into more subfolders based on metadata

See third-party-copyright-stuff.txt for third party stuff used, I can't figure out if I'm supposed to put that in the main LICENSE file or if that's supposed to be like that, I can't get GitHub to recognize the MIT license last time I tried anyway.

That's all for this readme, I hope it made any sense whatsoever. Keep on meowing, gamers.
