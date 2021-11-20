from collections.abc import Collection, MutableSequence
from typing import Optional, Union

from meowlauncher.util.utils import pluralize


class Controller():
	def describe(self) -> str:
		return type(self).__name__

	@property
	def is_standard(self) -> bool:
		return False

class NormalController(Controller):
	def __init__(self) -> None:
		self.face_buttons = 0
		self.shoulder_buttons = 0
		self.dpads = 0
		self.analog_sticks = 0
		self.analog_triggers = 0

	@property
	def is_standard(self) -> bool:
		"""
		If this input setup is compatible with a standard modern controller: 4 face buttons, 2 shoulder buttons, 2 analog triggers, 2 analog sticks, one dpad, start + select. Dunno how I feel about clickable analog sticks. Also any "guide" or "home" button doesn't count, because that should be free for emulator purposes instead of needing the game to map to it. Hmm. Maybe analog triggers aren't that standard. Some modern gamepads just have 2 more shoulder buttons instead, after all.
		So if your gamepad has more stuff than this "standard" one, which it probably does, that's great, it just means it can support non-standard emulated controls.
		"""

		if self.analog_sticks > 2:
			return False
		if self.dpads > 1:
			if (self.analog_sticks + self.dpads) > 3:
				#It's okay to have two digital joysticks if one can just be mapped to one of the analog sticks
				return False

		if self.face_buttons > 4:
			return False

		if self.shoulder_buttons > 2:
			if (self.shoulder_buttons + self.analog_triggers) > 4:
				#It's okay to have 4 shoulder buttons if two can be mapped to the analog triggers
				return False

		if self.analog_triggers > 2:
			#Anything more than that is definitely non-standard, regardless of how I go with my "are analog triggers standard" debate
			return False

		return True

	def describe(self) -> str:
		description = set()
		if self.face_buttons:
			description.add(pluralize(self.face_buttons, 'button'))
		if self.shoulder_buttons:
			description.add(pluralize(self.shoulder_buttons, 'shoulder button'))
		if self.dpads:
			description.add(pluralize(self.dpads, 'dpad'))
		if self.analog_sticks:
			description.add(pluralize(self.analog_sticks, 'analog stick'))
		if self.analog_triggers:
			description.add(pluralize(self.analog_triggers, 'analog trigger'))

		return ' + '.join(description)

class Biological(Controller):
	#e.g. Mindlink for Atari 2600 (actually just senses muscle movement); N64 heart rate sensor
	pass

class Dial(Controller):
	def __init__(self) -> None:
		self.buttons = 0

	def describe(self) -> str:
		if self.buttons > 0:
			return f'{self.buttons}-button dial'
		return 'Dial'

class Gambling(Controller):
	def __init__(self) -> None:
		self.buttons = 0

	def describe(self) -> str:
		if self.buttons > 0:
			return f'{self.buttons}-button gambling controls'
		return 'Gambling Controls'

class Hanafuda(Controller):
	def __init__(self) -> None:
		self.buttons = 0 #Or are they more accurately called keys

	def describe(self) -> str:
		if self.buttons > 0:
			return f'{self.buttons}-button hanafuda controller'
		return 'Hanafuda Controller'

class Keyboard(Controller):
	def __init__(self) -> None:
		self.keys = 0

	def describe(self) -> str:
		if self.keys > 0:
			return f'{self.keys}-key keyboard'
		return 'Keyboard'

class Keypad(Controller):
	def __init__(self) -> None:
		self.keys = 0

	def describe(self) -> str:
		if self.keys > 0:
			return f'{self.keys}-key keypad'
		return 'Keypad'

class LightGun(Controller):
	def __init__(self) -> None:
		self.buttons = 0

	def describe(self) -> str:
		if self.buttons > 0:
			return f'{self.buttons}-button light gun'
		return 'Light Gun'

class Mahjong(Controller):
	def __init__(self) -> None:
		self.buttons = 0 #Or are they more accurately called keys (is this even really a different controller type anyway?)

	def describe(self) -> str:
		if self.buttons > 0:
			return f'{self.buttons}-button mahjong controller'
		return 'Mahjong Controller'

class MotionControls(Controller):
	def describe(self) -> str:
		return 'Motion Controls'

class Mouse(Controller):
	def __init__(self) -> None:
		self.buttons = 0

	def describe(self) -> str:
		if self.buttons > 0:
			return f'{self.buttons}-button mouse'
		return 'Mouse'

class Paddle(Controller):
	def __init__(self) -> None:
		self.buttons = 0

	def describe(self) -> str:
		if self.buttons > 0:
			return f'{self.buttons}-button paddle'
		return 'Paddle'

class Pedal(Controller):
	pass

class Positional(Controller):
	#What the heck is this
	pass

class SteeringWheel(Controller):
	def describe(self) -> str:
		return 'Steering Wheel'

class Touchscreen(Controller):
	pass

class Trackball(Controller):
	def __init__(self) -> None:
		self.buttons = 0

	def describe(self) -> str:
		if self.buttons > 0:
			return f'{self.buttons}-button trackball'
		return 'Trackball'

class Custom(Controller):
	def __init__(self, custom_description=None) -> None:
		self.custom_description = custom_description

	def describe(self) -> str:
		return self.custom_description if self.custom_description else 'Custom'

class CombinedController(Controller):
	def __init__(self, components: MutableSequence[Controller]=None) -> None:
		#TODO: Components probably shouldn't need to be a list since the order is unimportant but I'd need to readjust a few classes
		self.components: MutableSequence = []
		if components:
			self.components.extend(components)

	@property
	def is_standard(self) -> bool:
		return all(component.is_standard for component in self.components)

	def describe(self) -> str:
		if not self.components:
			#Theoretically shouldn't happen. $2 says I will be proven wrong and have to delete this comment
			return '<weird controller>'
		if len(self.components) == 1:
			return self.components[0].describe()
		return ' + '.join(component.describe() for component in self.components)

class InputOption():
	def __init__(self) -> None:
		#TODO: This should logically be a Collection as the order is not relevant, but some things in games.specific_behaviours like to mutate it, so that's not nice I guess
		self.inputs: MutableSequence[Controller] = []

	@property
	def is_standard(self):
		#Hmm could this be wrong... feel like there's a case I'm not thinking of right now where something could be standard inputs individually but not usable with standard controllers when all together
		return all(input.is_standard for input in self.inputs)

	def describe(self) -> str:
		if not self.inputs:
			return 'Nothing'
		return ' + '.join(input.describe() for input in self.inputs)

class InputInfo():
	def __init__(self) -> None:
		self.input_options: MutableSequence[InputOption] = []
		#Allows us to say that something explicitly has 0 inputs, admittedly not used opften
		self._is_inited = False

	def add_option(self, inputs: Union[Collection[Controller], Controller]):
		#TODO: Should inputs ever really be iterable? Or should I be using CombinedController in those instances (SCV, ScummVM, Atari 8 bit)
		opt = InputOption()
		opt.inputs = list(inputs) if isinstance(inputs, Collection) else [inputs]
		self.input_options.append(opt)

	@property
	def is_inited(self) -> bool:
		return bool(self.input_options) or self._is_inited

	def set_inited(self) -> None:
		self._is_inited = True

	@property
	def has_standard_inputs(self) -> bool:
		return any(option.is_standard for option in self.input_options) or not self.input_options

	def describe(self) -> Optional[Collection[str]]:
		return {opt.describe().capitalize() for opt in self.input_options} if self.input_options else {'Nothing'}
