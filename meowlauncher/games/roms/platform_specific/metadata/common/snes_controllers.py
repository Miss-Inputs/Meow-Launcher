from meowlauncher import input_metadata

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

#Other controllers: Miracle Piano (same as NES?)
#Stuff not available as MAME slot device: That horse racing numpad thingo
#Barcode Battler goes in the controller slot but from what I can tell it's not really a controller?
