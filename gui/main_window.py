import os
from threading import Thread

import wx
import wx.adv

from common_types import ConfigValueType
import config
import mame_helpers
import scummvm
import steam
import main

from .gui_generated import MeowLauncherGui

start_work_event_type = wx.NewEventType()
start_work_event_binder = wx.PyEventBinder(start_work_event_type)
work_done_event_type = wx.NewEventType()
work_done_event_binder = wx.PyEventBinder(work_done_event_type)
progress_event_type = wx.NewEventType()
progress_event_binder = wx.PyEventBinder(progress_event_type)

class StartWorkEvent(wx.PyCommandEvent):
	def __init__(self):
		super().__init__(start_work_event_type)

class WorkDoneEvent(wx.PyCommandEvent):
	def __init__(self):
		super().__init__(work_done_event_type)

class ProgressEvent(wx.PyCommandEvent):
	def __init__(self, data, should_increment):
		super().__init__(progress_event_type)
		self.data = data
		self.should_increment = should_increment

class WorkerThread(Thread):
	def __init__(self, wx_object, enabled_state):
		super().__init__()
		self.wx_object = wx_object
		self.enabled_state = enabled_state

	def send_progress_event(self, data, should_increment):
		event = ProgressEvent(data, should_increment)
		wx.PostEvent(self.wx_object, event)

	def run(self):
		start_event = StartWorkEvent()
		wx.PostEvent(self.wx_object, start_event)
		main.main(self.send_progress_event, *self.enabled_state)
		done_event = WorkDoneEvent()
		wx.PostEvent(self.wx_object, done_event)

def create_editor_for_config(parent, config_name, config_value, current_value):
	if config_value.type == ConfigValueType.Bool:
		check_box = wx.CheckBox(parent, label=config_value.name, name=config_name)
		check_box.Value = current_value
		check_box.SetToolTip(config_value.description)
		return check_box
	elif config_value.type == ConfigValueType.String:
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		label = wx.StaticText(parent, label=config_value.name)
		sizer.Add(label, 0, wx.ALL, 2)
		text_editor = wx.TextCtrl(parent, name=config_name)
		text_editor.Value = current_value
		text_editor.SetToolTip(config_value.description)
		sizer.Add(text_editor, 1, wx.ALL | wx.EXPAND, 2)
		return sizer
	elif config_value.type in (ConfigValueType.FilePath, ConfigValueType.FolderPath):
		sizer = wx.BoxSizer(wx.HORIZONTAL)
		label = wx.StaticText(parent, label=config_value.name)
		sizer.Add(label, 0, wx.ALL, 2)
		if config_value.type == ConfigValueType.FilePath:
			picker = wx.FilePickerCtrl(parent, name=config_name, style=wx.FLP_DEFAULT_STYLE | wx.FLP_USE_TEXTCTRL)
		else:
			picker = wx.DirPickerCtrl(parent, name=config_name, style=wx.DIRP_USE_TEXTCTRL | wx.DIRP_USE_TEXTCTRL)
		picker.Path = current_value
		picker.SetToolTip(config_value.description)
		sizer.Add(picker, 1, wx.ALL | wx.EXPAND, 2)
		return sizer
	elif config_value.type == ConfigValueType.StringList:
		editor = wx.adv.EditableListBox(parent, label=config_value.name, name=config_name)
		editor.SetStrings(current_value)
		editor.SetToolTip(config_value.description)
		return editor
	#FilePathList and FolderPathList currently aren't used. Hmm... dunno what would be the best way to implement them anyway
	return None

class MainWindow(MeowLauncherGui):
	def __init__(self, parent):
		super().__init__(parent)
		self.optionsSizer = self.optionsPanel.GetSizer() #wxFormBuilder won't put it as a property of the main window object
		self.Icon = wx.Icon('gui/icon.png')
		self.setupStuff()

		self.workerThread = None
		self.Bind(start_work_event_binder, self.on_worker_started)
		self.Bind(work_done_event_binder, self.on_worker_done)
		self.Bind(progress_event_binder, self.on_progress)
		self.running_game_types = 0

	def setupStuff(self):
		self.setupMainButtons()
		self.setupRuntimeOptions()
		self.setupMainConfigOptions()
		self.setupSystemsList()
		self.loadIgnoredDirs()

	def setupRuntimeOptions(self):
		for name, opt in config.get_runtime_options().items():
			editor = create_editor_for_config(self.optionsPanel, name, opt, opt.default_value)
			if editor:
				self.optionsSizer.Add(editor, 0, wx.ALL, 5)

	def setupMainConfigOptions(self):
		for section, configs in config.get_config_ini_options().items():
			sizer = wx.StaticBoxSizer(wx.VERTICAL, self.mainConfigScrolledWindow, label=section)
			for name, config_value in configs.items():
				editor = create_editor_for_config(sizer.GetStaticBox(), name, config_value, getattr(config.main_config, name))
				if editor:
					sizer.Add(editor, 0, wx.ALL | wx.EXPAND, 2)
			self.mainConfigScrolledWindow.GetSizer().Add(sizer, 0, wx.ALL | wx.EXPAND, 5)

	def setupSystemsList(self):
		self.systemsList.AppendColumn('Name')
		self.systemsList.AppendColumn('Emulators')
		self.systemsList.AppendColumn('Paths')
		self.systemsList.AppendColumn('Specific config')

	def mainSaveButtonOnButtonClick(self, event):
		new_config_values = {}
		for section, configs in config.get_config_ini_options().items():
			new_config_values[section] = {}
			for name, config_item in configs.items():
				control = self.mainConfigScrolledWindow.FindWindowByName(name)
				if config_item.type in (ConfigValueType.Bool, ConfigValueType.String):
					new_value = control.Value
				elif config_item.type in (ConfigValueType.FilePath, ConfigValueType.FolderPath):
					new_value = control.Path
				elif config_item.type == ConfigValueType.StringList:
					new_value = control.GetStrings()
				#TODO: Implement File/FolderPathList when we actually use that
				new_config_values[section][name] = new_value
		config.write_new_main_config(new_config_values)
		config.main_config.reread_config()

	def mainRevertButtonOnButtonClick(self, event):
		config.main_config.reread_config()
		for v in config.get_config_ini_options().values():
			for name, config_item in v.items():
				control = self.mainConfigScrolledWindow.FindWindowByName(name)
				current_value = getattr(config.main_config, name)
				if config_item.type in (ConfigValueType.Bool, ConfigValueType.String):
					control.Value = current_value
				elif config_item.type in (ConfigValueType.FilePath, ConfigValueType.FolderPath):
					control.Path = current_value
				elif config_item.type == ConfigValueType.StringList:
					control.SetStrings(current_value)

	def setupMainButtons(self):
		self.mameMachineCheckBox.Enabled = mame_helpers.have_mame()
		#Is there any condition in which it would make sense to disable the "roms" check box?
		self.macCheckBox.Enabled = os.path.isfile(config.mac_ini_path)
		self.dosCheckBox.Enabled = os.path.isfile(config.dos_ini_path)
		self.scummvmCheckBox.Enabled = scummvm.have_something_vm()
		self.steamCheckBox.Enabled = steam.is_steam_available()

	def loadRuntimeOptions(self):
		for checkbox_sizer_item in self.optionsSizer.GetChildren():
			checkbox = checkbox_sizer_item.GetWindow()
			config.main_config.runtime_overrides[checkbox.Name] = checkbox.IsChecked()

	def loadIgnoredDirs(self):
		self.ignoredDirsList.Clear()
		self.ignoredDirsList.AppendItems(config.main_config.ignored_directories)

	def ignoredDirsAddButtonOnButtonClick(self, event):
		with wx.DirDialog(self) as folder_chooser:
			if folder_chooser.ShowModal() == wx.ID_OK:
				self.ignoredDirsList.Append(folder_chooser.GetPath())

	def ignoredDirsDelButtonOnButtonClick(self, event):
		selection = self.ignoredDirsList.GetSelection()
		if selection != wx.NOT_FOUND:
			self.ignoredDirsList.Delete(selection)

	def ignoredDirsSaveButtonOnButtonClick(self, event):
		config.write_ignored_directories(self.ignoredDirsList.Items)
		config.main_config.reread_config()

	def ignoredDirsRevertButtonOnButtonClick(self, event):
		config.main_config.reread_config()
		self.loadIgnoredDirs()

	def okButtonOnButtonClick(self, event):
		self.loadRuntimeOptions()
		enabled_state = (self.mameMachineCheckBox.IsChecked(), self.romsCheckBox.IsChecked(), self.dosCheckBox.IsChecked(), self.macCheckBox.IsChecked(), self.scummvmCheckBox.IsChecked(), self.steamCheckBox.IsChecked())
		self.running_game_types = len([state for state in enabled_state if state])
		self.workerThread = WorkerThread(self, enabled_state)
		self.workerThread.start()

	def exitButtonOnButtonClick(self, event):
		self.Close()

	def on_worker_started(self, _):
		self.okButton.Disable()
		self.progressBar.Value = 0
		self.progressBar.Range = self.running_game_types + 5 #For the removing of old folder, remove non-existing games, series_detect, disambiguation, and organization of folders

	def on_worker_done(self, _):
		self.okButton.Enable()
		self.progressBar.Value = 0
		self.progressLabel.Label = 'Ready!'
		notification = wx.adv.NotificationMessage('Meow Launcher', 'Done creating launchers! Have fun!', self)
		notification.Show()

	def on_progress(self, event):
		if event.should_increment:
			self.progressBar.Value += 1
		if event.data:
			self.progressLabel.Label = event.data
