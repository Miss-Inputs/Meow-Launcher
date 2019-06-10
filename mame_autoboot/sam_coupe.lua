print(emu.gamename(), 'autoboot script in use')
for name, ioport in pairs(manager:machine():ioport().ports) do
	for field_name, field in pairs(ioport.fields) do
		if field_name == 'Space' then
			--This is just to get us off the little fancy colourful boot screen and into entering commands
			any_key_port = ioport
			any_key_field = field
		end
		if field_name == 'F9' then
			--Joystick down doesn't work for menu selection
			f9_key_port = ioport
			f9_key_field = field
		end
	end
end

button_press_counter = 0
button_press_frame_amount = 0
button_press_field = ""

local function check_unpress_button()
	if (button_press_counter + button_press_frame_amount) < counter and button_press_field ~= "" then
		button_press_field:set_value(0)
		button_press_counter = 0
		button_press_frame_amount = 0
		button_press_field = ""
	end
end

local function press_button(field, frames)
	--TODO: If you mash a button every frame, this won't get around to unpressing the button until after you stop mashing. But I guess that should be fine.
	field:set_value(1)
	button_press_counter = counter
	button_press_frame_amount = frames
	button_press_field = field
end

local function unpress_button(field)
	field:set_value(0)
end

counter = 0

press_any_key = 120
press_boot_key = 123

local function on_frame()
	counter = counter + 1

	--if any_key_field and counter < press_any_key_end_time then
	if any_key_field and counter == press_any_key then
		--Press a key when we are ready to start accepting commands
		--For whatever reason, it just seems it takes 120 frames for it to be ready, although this admittedly is a flaky way of doing this
		press_button(any_key_field, 1)
	end
	if f9_key_field and counter == press_boot_key then
		--Need to have at least 3 frames in between; if you do this on frame 121 or 122, the emulated machine won't unpress space
		press_button(f9_key_field, 1)
	end
	
	check_unpress_button()
end

emu.register_frame(on_frame)
