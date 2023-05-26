# Meow Launcher

## Disclaimer! For now

This project isn't in a state where it would really be useable by people who aren't me. I just haven't gotten around to any of that yet. Not configurable or flexible enough for my standards for me to say "yeah this is a release". It's just right now here just in case it is useful. Sort of on hiatus in the sense that you shouldn't expect this to be done at any point. I guess you just shouldn't anyway. But yeah it's just pre-pre-pre-pre-pre-release, you never know what might change, I might commit stuff which breaks everything, who knows. There is a 0.1 milestone on Github, which includes a lot of issues which are just me telling myself to go refactor something and so aren't really issues but that's just how I use the workflow I guess.

<img alt="Meow Launcher's logo" src="meowlauncher/icon.png?raw=true" width="300" />

Meow Launcher aims to transform games from various local sources (emulated or otherwise) into a launcher which takes care of what is compatible, what command line options need to be used, etc., you just launch the game, so you have one less obstacle in the process of playing a game and enjoying it.

## What does Meow Launcher do/not do?

Meow Launcher is not a game browser, that is intended to be a role fulfilled by something else; nor does it play any role in obtaining/updating games, or installing/configuring emulators or other related software. Meow Launcher attempts to somewhat follow the philosophy of "do one thing and do it well", and it is intended to have usable output for such software that would present you with a view of a "library" of games, or indeed your file manager/applications menu or other things that can run arbitrary applications.

In order to best achieve the goal of "determine what is the best way to run a certain game", Meow Launcher attempts to extract what information it can from a game without relying on online sources, this also allows me to enjoy being a massive nerd, but it should also assist any game browser that wants to let users filter games or display detailed info on them, or allow users to do that themselves for that matter.

Technically there is nothing stopping Meow Launcher stopping you from launching non-game software, but any documentation (or class names) make that assumption that you will be using it for entertainment. Meow Launcher does not demand that a game be "scraped" from some database for it to work, it merely attempts to use any databases it does find to assist finding interesting information.

Meow Launcher does include a list of emulators and emulated platforms that it knows it can use for a "just launch it and it works" experience, which does not include anything involving typing weird commands or anything like that (which excludes a lot of home microcomputer software). I'd like to close issue [#135](https://github.com/miss-inputs/Meow-Launcher/issues/135) and then get rid of this sentence that I'm typing now, but that's not done yet and that's one of the main reasons I have that disclaimer up there.

## The rest of the readme, which I am going to rewrite completely sorry and none of that is necessarily accurate

Basically it needs testing from other people. I use it daily when I feel like playing stuff, and I can say that it works enough for me, but if I were to say "yeah it works for me so it should work for everyone else" that'd be really stupid, wouldn't it? I encourage others to try it out if they have the patience to test experimental stuff (and they're interested in what it aims to do), but I imagine it would have several problems, probably among the lines of "my code expects this to exist in this place but it doesn't always exist there" and it breaks horribly. Maybe! I don't know. To my knowledge, nobody else has actually used it yet.

Anyway, don't be afraid to say "this is what I would like for Meow Launcher to be nice and useable for me", or something like that. Worst case scenario is that I will say "nah that's not what I wanna do" and then I don't do it, because it's a hobby project and I do what I want; but I do want to make something that helps people (that's why I'm here putting stuff on GitHub) and if I can make it work for you, then hey that's pretty cool.

Currently, Meow Launcher assumes that all emulators/cores that it launches are the most up to date version known, when considering what things an emulator can launch and what command line argument it uses, etc. This isn't a guarantee that things are up to date, it's just a lack of guarantee that old versions of emulators will continue to work just fine. For now. Perhaps if there is enough reason for me to bother, I could have some kind of option for each emulator that uses old behaviours/arguments…

Windows (as in running Meow Launcher on Windows, not necessarily emulating Windows) is kinda planned at some point in the distant future. Just haven't really felt that much of a reason to do it, and with less reason to ever run Windows…

Things untested and might break (but they might not!) but they are scenarios I thought of that I don't care enough about yet
	- Symlinks in ROM folders

TODO: Incorporate stuff.txt, which should not be a separate file, but it needs rewriting

The other things that you should know is that Pillow is required to extract icons and other images from ROMs that have those embedded (DS, 3DS, etc); and steamfiles is required for Steam games to work. That's all in requirements.txt anyway.

TODO: Go into more detail on game sources:
So, what games does Meow Launcher launch, anyway? Should I have put this part somewhere up there? Maybe!

- MAME machines (arcade games, but also plug & play games or Game & Watch or what have you), what you actually have and none of that "unavailable" business
- ROMs to be launched by an emulator
- Games with source ports (Doom, Quake); these are treated like pseudo-ROMs
- Aforementioned DOS and Mac that are a bit weird right now
- ScummVM (whatever you have added to your ScummVM config already)
- Steam, if you have that installed; not non-Steam game shortcuts because that would get weird

In progress is MAME software but I haven't done that yet.

TODO: Describe the config files in more detail: (this is now wrong I guess?)

- config.ini: General configuration
- emulators.ini: Config files for emulators
- platforms.ini: For ROMs, specifies where you put them, and also what emulators you want to use
- ignored_directories.txt: Skip over these directories (one per line) (config.py also does this sort of thing, so maybe I should put that into there)

TODO: Describe the command line arguments that are actually important, but for now, I'll mention these:

- --full-rescan: Normally Meow Launcher leaves your existing launchers alone (unless they refer to games that aren't there anymore), and only adds launchers for what isn't there since last time; this just avoids all that and throws the whole output folder out and starts again anew
- --print-times prints how long everything takes, which is also something you might not care about
- --organize-folders sorts your games into more subfolders based on info
- How long levels are used, for now:
	- Debug: Interesting thing about a game and can probs be ignored
	- Info: Something weird/broken about a game (ROM with unexpected header value, unexpected info for native game, etc) (but this isn't necessarily the user's fault so I felt nahhhh shouldn't be warning)
	- Warning: Config warning, or EmulationNotSupportedException, or something broken/unusable about a game that might be the user's problem
	- Error: aaaaaa

See third-party-copyright-stuff.txt for third party stuff used, because I feel like that should go somewhere, even if it's not redistributing anything else.

That's all for this readme, I hope it made any sense whatsoever. Keep on meowing, gamers.
