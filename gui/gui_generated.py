# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version Feb 17 2019)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc

###########################################################################
## Class MeowLauncherGui
###########################################################################

class MeowLauncherGui ( wx.Frame ):

	def __init__( self, parent ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"Meow Launcher", pos = wx.DefaultPosition, size = wx.Size( 700,500 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

		guiSizer = wx.BoxSizer( wx.VERTICAL )

		self.configNotebook = wx.Notebook( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.mainPanel = wx.Panel( self.configNotebook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		mainPanelSizer = wx.BoxSizer( wx.HORIZONTAL )

		gameTypesSizer = wx.StaticBoxSizer( wx.StaticBox( self.mainPanel, wx.ID_ANY, u"Game Types" ), wx.VERTICAL )

		self.mameMachineCheckBox = wx.CheckBox( gameTypesSizer.GetStaticBox(), wx.ID_ANY, u"MAME machines", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.mameMachineCheckBox.SetValue(True)
		gameTypesSizer.Add( self.mameMachineCheckBox, 0, wx.ALL, 5 )

		self.romsCheckBox = wx.CheckBox( gameTypesSizer.GetStaticBox(), wx.ID_ANY, u"Roms", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.romsCheckBox.SetValue(True)
		gameTypesSizer.Add( self.romsCheckBox, 0, wx.ALL, 5 )

		self.dosCheckBox = wx.CheckBox( gameTypesSizer.GetStaticBox(), wx.ID_ANY, u"DOS", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.dosCheckBox.SetValue(True)
		gameTypesSizer.Add( self.dosCheckBox, 0, wx.ALL, 5 )

		self.macCheckBox = wx.CheckBox( gameTypesSizer.GetStaticBox(), wx.ID_ANY, u"Mac", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.macCheckBox.SetValue(True)
		gameTypesSizer.Add( self.macCheckBox, 0, wx.ALL, 5 )

		self.scummvmCheckBox = wx.CheckBox( gameTypesSizer.GetStaticBox(), wx.ID_ANY, u"ScummVM", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.scummvmCheckBox.SetValue(True)
		gameTypesSizer.Add( self.scummvmCheckBox, 0, wx.ALL, 5 )

		self.steamCheckBox = wx.CheckBox( gameTypesSizer.GetStaticBox(), wx.ID_ANY, u"Steam", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.steamCheckBox.SetValue(True)
		gameTypesSizer.Add( self.steamCheckBox, 0, wx.ALL, 5 )


		mainPanelSizer.Add( gameTypesSizer, 1, wx.EXPAND, 5 )

		optionsSizer = wx.StaticBoxSizer( wx.StaticBox( self.mainPanel, wx.ID_ANY, u"Options" ), wx.VERTICAL )


		mainPanelSizer.Add( optionsSizer, 1, wx.EXPAND, 5 )


		self.mainPanel.SetSizer( mainPanelSizer )
		self.mainPanel.Layout()
		mainPanelSizer.Fit( self.mainPanel )
		self.configNotebook.AddPage( self.mainPanel, u"Main", True )
		self.mainConfigPanel = wx.Panel( self.configNotebook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		mainConfigPanelSizer = wx.BoxSizer( wx.VERTICAL )

		mainButtonsSizer = wx.BoxSizer( wx.HORIZONTAL )

		self.mainSaveButton = wx.Button( self.mainConfigPanel, wx.ID_ANY, u"Save", wx.DefaultPosition, wx.DefaultSize, 0 )
		mainButtonsSizer.Add( self.mainSaveButton, 0, wx.ALL, 5 )

		self.mainRevertButton = wx.Button( self.mainConfigPanel, wx.ID_ANY, u"Revert", wx.DefaultPosition, wx.DefaultSize, 0 )
		mainButtonsSizer.Add( self.mainRevertButton, 0, wx.ALL, 5 )


		mainConfigPanelSizer.Add( mainButtonsSizer, 0, wx.EXPAND, 5 )

		self.mainConfigScrolledWindow = wx.ScrolledWindow( self.mainConfigPanel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.BORDER_THEME|wx.HSCROLL|wx.VSCROLL )
		self.mainConfigScrolledWindow.SetScrollRate( 5, 5 )
		mainConfigPanelSizer.Add( self.mainConfigScrolledWindow, 1, wx.EXPAND |wx.ALL, 5 )


		self.mainConfigPanel.SetSizer( mainConfigPanelSizer )
		self.mainConfigPanel.Layout()
		mainConfigPanelSizer.Fit( self.mainConfigPanel )
		self.configNotebook.AddPage( self.mainConfigPanel, u"Config", False )
		self.systemsConfigPanel = wx.Panel( self.configNotebook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		systemsConfigPanelSizer = wx.BoxSizer( wx.VERTICAL )

		systemsButtonsSizer = wx.BoxSizer( wx.HORIZONTAL )

		self.systemsSaveButton = wx.Button( self.systemsConfigPanel, wx.ID_ANY, u"Save", wx.DefaultPosition, wx.DefaultSize, 0 )
		systemsButtonsSizer.Add( self.systemsSaveButton, 0, wx.ALL, 5 )

		self.systemsRevertButton = wx.Button( self.systemsConfigPanel, wx.ID_ANY, u"Revert", wx.DefaultPosition, wx.DefaultSize, 0 )
		systemsButtonsSizer.Add( self.systemsRevertButton, 0, wx.ALL, 5 )


		systemsConfigPanelSizer.Add( systemsButtonsSizer, 0, wx.EXPAND, 5 )

		self.systemsConfigScrolledWindow = wx.ScrolledWindow( self.systemsConfigPanel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.BORDER_THEME|wx.HSCROLL|wx.VSCROLL )
		self.systemsConfigScrolledWindow.SetScrollRate( 5, 5 )
		systemsConfigPanelSizer.Add( self.systemsConfigScrolledWindow, 1, wx.EXPAND |wx.ALL, 5 )


		self.systemsConfigPanel.SetSizer( systemsConfigPanelSizer )
		self.systemsConfigPanel.Layout()
		systemsConfigPanelSizer.Fit( self.systemsConfigPanel )
		self.configNotebook.AddPage( self.systemsConfigPanel, u"Systems", False )
		self.ignoredDirsPanel = wx.Panel( self.configNotebook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		ignoredDirsPanelSizer = wx.BoxSizer( wx.VERTICAL )

		ignoredDirsSaveRevertButtonSizer = wx.BoxSizer( wx.HORIZONTAL )

		self.ignoredDirsSaveButton = wx.Button( self.ignoredDirsPanel, wx.ID_ANY, u"Save", wx.DefaultPosition, wx.DefaultSize, 0 )
		ignoredDirsSaveRevertButtonSizer.Add( self.ignoredDirsSaveButton, 0, wx.ALL, 5 )

		self.ignoredDirsRevertButton = wx.Button( self.ignoredDirsPanel, wx.ID_ANY, u"Revert", wx.DefaultPosition, wx.DefaultSize, 0 )
		ignoredDirsSaveRevertButtonSizer.Add( self.ignoredDirsRevertButton, 0, wx.ALL, 5 )


		ignoredDirsPanelSizer.Add( ignoredDirsSaveRevertButtonSizer, 0, wx.EXPAND, 5 )

		ignoredDirsEditorSizer = wx.BoxSizer( wx.HORIZONTAL )

		ignoredDirsListChoices = []
		self.ignoredDirsList = wx.ListBox( self.ignoredDirsPanel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, ignoredDirsListChoices, 0 )
		ignoredDirsEditorSizer.Add( self.ignoredDirsList, 1, wx.ALL|wx.EXPAND, 5 )

		ignoredDirsEditorButtonsSizer = wx.BoxSizer( wx.VERTICAL )

		self.ignoredDirsAddButton = wx.Button( self.ignoredDirsPanel, wx.ID_ANY, u"Add", wx.DefaultPosition, wx.DefaultSize, 0 )
		ignoredDirsEditorButtonsSizer.Add( self.ignoredDirsAddButton, 0, wx.ALL, 5 )

		self.ignoredDirsDelButton = wx.Button( self.ignoredDirsPanel, wx.ID_ANY, u"Delete", wx.DefaultPosition, wx.DefaultSize, 0 )
		ignoredDirsEditorButtonsSizer.Add( self.ignoredDirsDelButton, 0, wx.ALL, 5 )


		ignoredDirsEditorSizer.Add( ignoredDirsEditorButtonsSizer, 0, wx.EXPAND, 5 )


		ignoredDirsPanelSizer.Add( ignoredDirsEditorSizer, 1, wx.EXPAND, 5 )


		self.ignoredDirsPanel.SetSizer( ignoredDirsPanelSizer )
		self.ignoredDirsPanel.Layout()
		ignoredDirsPanelSizer.Fit( self.ignoredDirsPanel )
		self.configNotebook.AddPage( self.ignoredDirsPanel, u"Ignored Directories", False )

		guiSizer.Add( self.configNotebook, 1, wx.ALL|wx.EXPAND, 5 )

		buttonsSizer = wx.BoxSizer( wx.HORIZONTAL )

		self.okButton = wx.Button( self, wx.ID_ANY, u"Go!", wx.DefaultPosition, wx.DefaultSize, 0 )
		buttonsSizer.Add( self.okButton, 0, wx.ALIGN_BOTTOM|wx.ALL|wx.BOTTOM, 5 )

		self.exitButton = wx.Button( self, wx.ID_ANY, u"Exit", wx.DefaultPosition, wx.DefaultSize, 0 )
		buttonsSizer.Add( self.exitButton, 0, wx.ALIGN_BOTTOM|wx.ALL, 5 )


		guiSizer.Add( buttonsSizer, 0, wx.ALIGN_BOTTOM|wx.BOTTOM|wx.SHAPED, 5 )


		self.SetSizer( guiSizer )
		self.Layout()

		self.Centre( wx.BOTH )

		# Connect Events
		self.okButton.Bind( wx.EVT_BUTTON, self.okButtonOnButtonClick )
		self.exitButton.Bind( wx.EVT_BUTTON, self.exitButtonOnButtonClick )

	def __del__( self ):
		pass


	# Virtual event handlers, overide them in your derived class
	def okButtonOnButtonClick( self, event ):
		event.Skip()

	def exitButtonOnButtonClick( self, event ):
		event.Skip()


