import os

import wx

import config
import dos
import mac
import mame_helpers
import mame_machines
import roms
import scummvm
import steam
import remove_nonexistent_games
import disambiguate

from .gui_generated import MeowLauncherGui

def doTheThing(mame_checked, roms_checked, dos_checked, mac_checked, scummvm_checked, steam_checked):
	if config.main_config.full_rescan:
		if os.path.isdir(config.main_config.output_folder):
			for f in os.listdir(config.main_config.output_folder):
				os.unlink(os.path.join(config.main_config.output_folder, f))
	os.makedirs(config.main_config.output_folder, exist_ok=True)

	if mame_checked:
		mame_machines.process_arcade()
	if roms_checked:
		roms.process_systems()
	if mac_checked:
		mac.make_mac_launchers()
	if dos_checked:
		dos.make_dos_launchers()
	if scummvm_checked:
		scummvm.add_scummvm_games()
	if steam_checked:
		steam.process_steam()

	if not config.main_config.full_rescan:
		remove_nonexistent_games.remove_nonexistent_games()

	disambiguate.disambiguate_names()


class MainWindow(MeowLauncherGui):
	def __init__(self, parent):
		super().__init__(parent)
		self.optionsPanel = self.FindWindowByName('optionsPanel')
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
			self.optionsSizer.Add(checkbox)

	def setupMainButtons(self):
		self.mameMachineCheckBox.Enabled = mame_helpers.have_mame()
		#Is there any condition in which it would make sense to disable the "roms" check box?
		self.macCheckBox.Enabled = os.path.isfile(config.mac_ini_path)
		self.dosCheckBox.Enabled = os.path.isfile(config.dos_ini_path)
		self.scummvmCheckBox.Enabled = scummvm.have_something_vm()
		self.steamCheckBox.Enabled = steam.is_steam_available()

	def okButtonOnButtonClick(self, event):
		doTheThing(self.mameMachineCheckBox.IsChecked(), self.romsCheckBox.IsChecked(), self.dosCheckBox.IsChecked(), self.macCheckBox.IsChecked(), self.scummvmCheckBox.IsChecked(), self.steamCheckBox.IsChecked())

	def exitButtonOnButtonClick(self, event):
		self.Close()
