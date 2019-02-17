from .gui_generated import MeowLauncherGui

import os

import wx

import config
import mame_helpers
import scummvm
import steam

class MainWindow(MeowLauncherGui):
	def __init__(self, parent):
		super().__init__(parent)
		self.Icon = wx.Icon('gui/icon.png')
		self.setupStuff()

	def setupStuff(self):
		self.setupMainButtons()

	def setupMainButtons(self):
		self.mameMachineCheckBox.Enabled = mame_helpers.have_mame()
		#Is there any condition in which it would make sense to disable the "roms" check box?
		self.macCheckBox.Enabled = os.path.isfile(config.mac_ini_path)
		self.dosCheckBox.Enabled = os.path.isfile(config.dos_ini_path)
		self.scummvmCheckBox.Enabled = scummvm.have_something_vm()
		self.steamCheckBox.Enabled = steam.is_steam_available()

	def okButtonOnButtonClick(self, event):
		return super().okButtonOnButtonClick(event)

	def exitButtonOnButtonClick(self, event):
		self.Close()
