# Crappy Game Launcher

Hello! This sucks.

The purpose of this is to launch games, generally of the emulated variety. And it does that by creating .desktop files and such, which are the most standardized launchers you can have, really.

You can use the --organize-folders command line option to put those desktop files into folders that can be used as though it was a nice little frontend, or you can put them into... some other frontend, I dunno. You could put them into your actual applications menu if you wanted your applications menu to be really big.

Anyway, it just aims to be the simplest thing possible. As long as it works.

It is just here in the unlikely event that it is useful to anyone; it will probably not be directly, because it is configured for my own computer specifically. I mean, you can change those paths, but yeah. Not a single bit of effort or thought has gone into cross-platformability or cross...other-people's-computers-ability.

Basically, it's my plan that you change everything you need in config.py, and then run main.py, and then everything just happens in the simplest way possible.

Create a file called "ignored_directories.txt" next to config.py with each line being a full path ending with a slash, and you can skip over directories that you don't want turned into launchers even if they have ROMs in them.

I'm really bad at wording things, so hopefully that all made sense.

Well, so far, there is one way in which it actually tries to run on more than one computer: You will see multiple references to "toasters" in the code, which refers to a computer that is horrendously underpowered (in my case, it is a netbook).

Note that PokeMini is wrapped in a shell script named "PokeMini.sh" that temporarily goes to ~/.config/PokeMini because otherwise it just dumps its config right in whatever the current directory is, and I don't like that nor do I know how it would even work out with .desktop files. Other emulators are used untouched, and you can look in config.py to see what it uses (or change them to something else of your liking).