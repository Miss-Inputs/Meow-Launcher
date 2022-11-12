from meowlauncher import input_metadata

__doc__ = """Contains input_metadata.Controller info for SNES controllers, which are shared between both SNES and Uzebox
Other controllers: Miracle Piano (same as NES?)
Stuff not available as MAME slot device so it wuoldn't appear in software lists so we have no way of getting that information I guess… wait we don't get that information anyway: That horse racing numpad thingo
Barcode Battler goes in the controller slot but from what I can tell it's not really a controller?
"""

controller = input_metadata.NormalController()
controller.dpads = 1
controller.face_buttons = 4 #also Select + Start
controller.shoulder_buttons = 2

mouse = input_metadata.Mouse()
mouse.buttons = 2

gun = input_metadata.LightGun() #pew pew
gun.buttons = 2 #Also pause and turbo

pachinko = input_metadata.Paddle()
pachinko.buttons = 1
