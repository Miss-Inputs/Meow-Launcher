import os
from threading import Thread

import wx
import wx.adv

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
	if config_value.type == config.ConfigValueType.Bool:
		check_box = wx.CheckBox(parent, label=config_value.name, name=config_name)
		check_box.Value = current_value
		check_box.SetToolTip(config_value.description)
		return check_box
	elif config_value.type == config.ConfigValueType.String:
		sizer = wx.BoxSizer(wx.VERTICAL)
		label = wx.StaticText(parent, label=config_value.name)
		sizer.Add(label, 0, wx.ALL, 2)
		text_editor = wx.TextCtrl(parent, name=config_name)
		text_editor.Value = current_value
		text_editor.SetToolTip(config_value.description)
		sizer.Add(text_editor, 0, wx.ALL | wx.EXPAND, 2)
		return sizer
	elif config_value.type == config.ConfigValueType.Path:
		sizer = wx.BoxSizer(wx.VERTICAL)
		label = wx.StaticText(parent, label=config_value.name)
		sizer.Add(label, 0, wx.ALL, 2)
		picker = wx.FilePickerCtrl(parent, name=config_name, style=wx.FLP_DEFAULT_STYLE | wx.FLP_USE_TEXTCTRL)
		picker.Path = current_value
		picker.SetToolTip(config_value.description)
		sizer.Add(picker, 0, wx.ALL | wx.EXPAND, 2)
		return sizer
	#elif config_value.type == config.ConfigValueType.StringList:
	#	return None
	#elif config_value.type == config.ConfigValueType.PathList:
	#	return None
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
				print(section, name, config_value.name, config_value.type, config_value.description, config_value.default_value)
				editor = create_editor_for_config(sizer.GetStaticBox(), name, config_value, getattr(config.main_config, name))
				if editor:
					sizer.Add(editor, 0, wx.ALL | wx.EXPAND, 2)
					sizer.Add(wx.StaticLine(sizer.GetStaticBox()), 0, wx.ALL | wx.EXPAND, 2)
			self.mainConfigScrolledWindow.GetSizer().Add(sizer, 0, wx.ALL | wx.EXPAND, 5)

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
		self.progressBar.Range = self.running_game_types + 4 #For the removing of old folder, remove non-existing games, disambiguation, and organization of folders

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
