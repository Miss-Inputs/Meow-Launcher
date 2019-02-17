#!/usr/bin/env python3

import wx

from gui.main_window import MainWindow

app = wx.App()

main_frame = MainWindow(None)
main_frame.Show()

app.MainLoop()
