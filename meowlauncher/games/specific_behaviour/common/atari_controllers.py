"""Stuff that goes in the Atari joystick port, shared across most Atari systems"""
from meowlauncher import input_info

joystick = input_info.NormalController()
joystick.dpads = 1
joystick.face_buttons = 1

boostergrip = input_info.NormalController()
boostergrip.dpads = 1
boostergrip.face_buttons = 3

paddle = input_info.Paddle()
"""Note that this is 2 paddles per port"""
paddle.buttons = 2

keypad = input_info.Keypad()
keypad.keys = 12

compumate = input_info.Keyboard()
compumate.keys = 42

mindlink = input_info.Biological()

driving_controller = input_info.SteeringWheel()

atari_st_mouse = input_info.Mouse()
atari_st_mouse.buttons = 2

xegs_gun = input_info.LightGun()
xegs_gun.buttons = 1

cx22_trackball = input_info.Trackball()
cx22_trackball.buttons = 1 #Physically 2, but functionally 1 (they are there to be ambidextrous)

#No, but also yes
megadrive_pad = input_info.NormalController()
megadrive_pad.face_buttons = 3
megadrive_pad.dpads = 1
