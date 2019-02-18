import os

import wx

import config
import mame_helpers
import scummvm
import steam
import main

from .gui_generated import MeowLauncherGui

class MainWindow(MeowLauncherGui):
	def __init__(self, parent):
		super().__init__(parent)
		self.optionsSizer = self.optionsPanel.GetSizer() #wxFormBuilder won't put it as a property of the main window object
		self.Icon = wx.Icon('gui/icon.png')
		self.setupStuff()

	def setupStuff(self):
		self.setupMainButtons()
		self.setupRuntimeOptions()

	def setupRuntimeOptions(self):
		for name, opt in config.get_runtime_options().items():
			#TODO These might not always be bools
			checkbox = wx.CheckBox(self.optionsPanel, name=name, label=opt.name)
			checkbox.Value = opt.default_value
			checkbox.SetToolTip(wx.ToolTip(opt.description))
			self.optionsSizer.Add(checkbox, 0, wx.ALL, 5)

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

	def okButtonOnButtonClick(self, event):
		self.loadRuntimeOptions()
		main.main(self.mameMachineCheckBox.IsChecked(), self.romsCheckBox.IsChecked(), self.dosCheckBox.IsChecked(), self.macCheckBox.IsChecked(), self.scummvmCheckBox.IsChecked(), self.steamCheckBox.IsChecked())

	def exitButtonOnButtonClick(self, event):
		self.Close()
