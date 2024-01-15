print(emu.gamename(), 'autoboot script in use')
for name, ioport in pairs(manager:machine():ioport().ports) do
	for field_name, field in pairs(ioport.fields) do
		if field_name == 'P1 Button 1' then
			--Actually, you could just press the any key...
			button_1_port = ioport
			button_1_field = field
		end
		if field_name == 'Down' then
			--Joystick down doesn't work for menu selection
			down_port = ioport
			down_field = field
		end
		if field_name == 'RT' then
			return_port = ioport
			return_field = field
		end
	end
end

button_press_counter = 0
button_press_frame_amount = 0
button_press_field = ""

local function check_unpress_button()
	if (button_press_counter + button_press_frame_amount) < counter and button_press_field ~= "" then
--		print('Unpressing', button_press_field.name, 'at frame', counter)
		button_press_field:set_value(0)
		button_press_counter = 0
		button_press_frame_amount = 0
		button_press_field = ""
	end
end

local function press_button(field, frames)
	--TODO: If you mash a button every frame, this won't get around to unpressing the button until after you stop mashing. But I guess that should be fine.
	--print('Pressing', field.name, 'at frame', counter, 'with frames =', frames)
	field:set_value(1)
	button_press_counter = counter
	button_press_frame_amount = frames
	button_press_field = field
end

local function unpress_button(field)
	print('Unpressing', field.name, 'at frame', counter)
	field:set_value(0)
end

counter = 1

mash_button_1_end_time = 100
press_down_first_time = 160
press_down_second_time = press_down_first_time + 3
press_return = press_down_second_time + 2
local function on_frame()
	counter = counter + 1

	if button_1_field and counter < mash_button_1_end_time then
		--Mash button 1 until we get to the menu
		--TODO: Instead of relying on strict timing, somehow read the graphics RAM or something
		press_button(button_1_field, 2)
	end
	if down_field and counter == press_down_first_time or counter == press_down_second_time then
		--Seems to require 2 seconds overall to get to the menu...
		press_button(down_field, 1)
	end
	if return_field and counter == press_return then
		press_button(return_field, 1)
	end
	check_unpress_button()
end

print(button_1_port, button_1_field)
print(down_port, down_field)
print(return_port, return_field)
emu.register_frame(on_frame)
