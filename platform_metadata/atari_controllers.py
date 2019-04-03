import input_metadata

#Stuff that goes in the Atari joystick port, shared across most Atari systems

joystick = input_metadata.NormalController()
joystick.dpads = 1
joystick.face_buttons = 1

boostergrip = input_metadata.NormalController()
boostergrip.dpads = 1
boostergrip.face_buttons = 3

paddle = input_metadata.Paddle()
#Note that this is 2 paddles per port
paddle.buttons = 2

keypad = input_metadata.Keypad()
keypad.keys = 12

compumate = input_metadata.Keyboard()
compumate.keys = 42

mindlink = input_metadata.Biological()

driving_controller = input_metadata.SteeringWheel()

atari_st_mouse = input_metadata.Mouse()
atari_st_mouse.buttons = 2

xegs_gun = input_metadata.LightGun()
xegs_gun.buttons = 1

cx22_trackball = input_metadata.Trackball()
cx22_trackball.buttons = 1 #Physically 2, but functionally 1 (they are there to be ambidextrous)
