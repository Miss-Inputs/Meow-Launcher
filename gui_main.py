#!/usr/bin/env python3

import wx

from gui.gui_generated import Gui

app = wx.App()

main_frame = Gui(None)
main_frame.Show()

app.MainLoop()
