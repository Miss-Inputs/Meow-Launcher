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
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"Meow Launcher", pos = wx.DefaultPosition, size = wx.Size( 640,480 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

		self.SetSizeHints( wx.Size( 640,480 ), wx.DefaultSize )

		guiSizer = wx.BoxSizer( wx.VERTICAL )

		self.configNotebook = wx.Notebook( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.mainPanel = wx.Panel( self.configNotebook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		mainPanelSizer = wx.BoxSizer( wx.HORIZONTAL )

		self.gameTypesPanel = wx.Panel( self.mainPanel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL, u"gameTypesPanel" )
		gameTypesSizer = wx.StaticBoxSizer( wx.StaticBox( self.gameTypesPanel, wx.ID_ANY, u"Game Types" ), wx.VERTICAL )

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


		self.gameTypesPanel.SetSizer( gameTypesSizer )
		self.gameTypesPanel.Layout()
		gameTypesSizer.Fit( self.gameTypesPanel )
		mainPanelSizer.Add( self.gameTypesPanel, 1, wx.EXPAND |wx.ALL, 5 )

		self.optionsPanel = wx.Panel( self.mainPanel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL, u"optionsPanel" )
		optionsSizer = wx.StaticBoxSizer( wx.StaticBox( self.optionsPanel, wx.ID_ANY, u"Options" ), wx.VERTICAL )


		self.optionsPanel.SetSizer( optionsSizer )
		self.optionsPanel.Layout()
		optionsSizer.Fit( self.optionsPanel )
		mainPanelSizer.Add( self.optionsPanel, 1, wx.EXPAND |wx.ALL, 5 )


		self.mainPanel.SetSizer( mainPanelSizer )
		self.mainPanel.Layout()
		mainPanelSizer.Fit( self.mainPanel )
		self.configNotebook.AddPage( self.mainPanel, u"Main", False )
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
		self.configNotebook.AddPage( self.ignoredDirsPanel, u"Ignored Directories", True )

		guiSizer.Add( self.configNotebook, 1, wx.ALL|wx.EXPAND, 5 )

		self.progressPanel = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		progressSizer = wx.BoxSizer( wx.VERTICAL )

		self.progressLabel = wx.StaticText( self.progressPanel, wx.ID_ANY, u"Ready!", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.progressLabel.Wrap( -1 )

		progressSizer.Add( self.progressLabel, 0, wx.ALL, 5 )

		self.progressBar = wx.Gauge( self.progressPanel, wx.ID_ANY, 9, wx.DefaultPosition, wx.DefaultSize, wx.GA_HORIZONTAL )
		self.progressBar.SetValue( 0 )
		progressSizer.Add( self.progressBar, 0, wx.ALL|wx.EXPAND, 5 )


		self.progressPanel.SetSizer( progressSizer )
		self.progressPanel.Layout()
		progressSizer.Fit( self.progressPanel )
		guiSizer.Add( self.progressPanel, 0, wx.EXPAND |wx.ALL, 5 )

		buttonsSizer = wx.BoxSizer( wx.HORIZONTAL )

		self.okButton = wx.Button( self, wx.ID_ANY, u"Go!", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.okButton.SetToolTip( u"Start creating launchers" )

		buttonsSizer.Add( self.okButton, 0, wx.ALIGN_BOTTOM|wx.ALL|wx.BOTTOM, 5 )

		self.exitButton = wx.Button( self, wx.ID_ANY, u"Exit", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.exitButton.SetToolTip( u"Exit Meow Launcher" )

		buttonsSizer.Add( self.exitButton, 0, wx.ALIGN_BOTTOM|wx.ALL, 5 )


		guiSizer.Add( buttonsSizer, 0, wx.ALIGN_BOTTOM|wx.BOTTOM|wx.SHAPED, 5 )


		self.SetSizer( guiSizer )
		self.Layout()

		self.Centre( wx.BOTH )

		# Connect Events
		self.mainSaveButton.Bind( wx.EVT_BUTTON, self.mainSaveButtonOnButtonClick )
		self.mainRevertButton.Bind( wx.EVT_BUTTON, self.mainRevertButtonOnButtonClick )
		self.systemsSaveButton.Bind( wx.EVT_BUTTON, self.systemsSaveButtonOnButtonClick )
		self.systemsRevertButton.Bind( wx.EVT_BUTTON, self.systemsRevertButtonOnButtonClick )
		self.ignoredDirsSaveButton.Bind( wx.EVT_BUTTON, self.ignoredDirsSaveButtonOnButtonClick )
		self.ignoredDirsRevertButton.Bind( wx.EVT_BUTTON, self.ignoredDirsRevertButtonOnButtonClick )
		self.ignoredDirsAddButton.Bind( wx.EVT_BUTTON, self.ignoredDirsAddButtonOnButtonClick )
		self.ignoredDirsDelButton.Bind( wx.EVT_BUTTON, self.ignoredDirsDelButtonOnButtonClick )
		self.okButton.Bind( wx.EVT_BUTTON, self.okButtonOnButtonClick )
		self.exitButton.Bind( wx.EVT_BUTTON, self.exitButtonOnButtonClick )

	def __del__( self ):
		pass


	# Virtual event handlers, overide them in your derived class
	def mainSaveButtonOnButtonClick( self, event ):
		event.Skip()

	def mainRevertButtonOnButtonClick( self, event ):
		event.Skip()

	def systemsSaveButtonOnButtonClick( self, event ):
		event.Skip()

	def systemsRevertButtonOnButtonClick( self, event ):
		event.Skip()

	def ignoredDirsSaveButtonOnButtonClick( self, event ):
		event.Skip()

	def ignoredDirsRevertButtonOnButtonClick( self, event ):
		event.Skip()

	def ignoredDirsAddButtonOnButtonClick( self, event ):
		event.Skip()

	def ignoredDirsDelButtonOnButtonClick( self, event ):
		event.Skip()

	def okButtonOnButtonClick( self, event ):
		event.Skip()

	def exitButtonOnButtonClick( self, event ):
		event.Skip()


