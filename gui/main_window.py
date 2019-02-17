from .gui_generated import MeowLauncherGui

import wx

class MainWindow(MeowLauncherGui):
	def __init__(self, parent):
		super().__init__(parent)
		self.Icon = wx.Icon('gui/icon.png')

	def exitButtonOnButtonClick(self, event):
		self.Close()
