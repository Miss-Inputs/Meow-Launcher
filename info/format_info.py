#Basically just stuff shared between emulator_info and system_info tbh

mame_cdrom_formats = ['iso', 'chd', 'cue', 'toc', 'nrg', 'cdr', 'gdi']
#Some drivers have custom floppy formats, but these seem to be available for all
mame_floppy_formats = ['d77', 'd88', '1dd', 'dfi', 'hfe', 'imd', 'ipf', 'mfi', 'mfm', 'td0', 'cqm', 'cqi', 'dsk']

#File formats seem to be common between C64/VIC-20/PET/etc
commodore_disk_formats = ['d64', 'g64', 'x64', 'p64', 'd71', 'd81', 'd80', 'd82', 'd1m', 'd2m', 'dsk', 'ipf', 'nib']
#Would be better to just use crt everywhere, but sometimes that just doesn't happen and so the load address has to be stored in the extension
commodore_cart_formats = ['20', '40', '60', '70', '80', 'a0', 'b0', 'e0', 'crt', 'bin']
#There is also .cu which is some Harmony Cart format which might not work so easily… .ar is actually Supercharger which also might be different
atari_2600_cartridge_extensions = ['2k', '4k', 'f8', 'ef', 'efs', 'f4', 'f4s', 'fa', 'fe', '3f', '3e', '3ex', '3ep', '3e+', 'e0', 'f8s', 'f6', 'f6s', 'e7', 'cv', 'ua', 'ar', 'dpc', '084']

#Used where the extension doesn't really mean anything and it's just a generic ol' rom, but this is the file extensions that normal people use
#Ideally the usage of this would signifify to not try and use file extensions to detect type
generic_cart_extensions = ['bin', 'rom', 'u1', 'u3']

generic_tape_extensions = ['wav', 'tap', 'cas']

#All known possible CD-ROM formats, for use with file_types and MediaType.OpticalDisc; of course emulator support may vary
cdrom_formats = mame_cdrom_formats + ['cdi', 'ccd']
