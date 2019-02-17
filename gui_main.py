#!/usr/bin/env python3

import wx

from gui.gui_generated import Gui

app = wx.App()

class GuiInstance(Gui):
	def __init__(self, parent):
		super().__init__(parent)
		self.Icon = wx.Icon('gui/icon.png')


main_frame = GuiInstance(None)
main_frame.Show()

app.MainLoop()
