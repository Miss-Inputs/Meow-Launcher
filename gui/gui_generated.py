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
## Class Gui
###########################################################################

class Gui ( wx.Frame ):

	def __init__( self, parent ):
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = wx.EmptyString, pos = wx.DefaultPosition, size = wx.Size( 500,300 ), style = wx.DEFAULT_FRAME_STYLE|wx.TAB_TRAVERSAL )

		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

		bSizer2 = wx.BoxSizer( wx.VERTICAL )

		self.m_notebook3 = wx.Notebook( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.mainConfigPanel = wx.Panel( self.m_notebook3, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		mainConfigPanelSizer = wx.BoxSizer( wx.VERTICAL )

		mainButtonsSizer = wx.BoxSizer( wx.HORIZONTAL )

		self.mainSaveButton = wx.Button( self.mainConfigPanel, wx.ID_ANY, u"Save", wx.DefaultPosition, wx.DefaultSize, 0 )
		mainButtonsSizer.Add( self.mainSaveButton, 0, wx.ALL, 5 )

		self.mainRevertButton = wx.Button( self.mainConfigPanel, wx.ID_ANY, u"Revert", wx.DefaultPosition, wx.DefaultSize, 0 )
		mainButtonsSizer.Add( self.mainRevertButton, 0, wx.ALL, 5 )


		mainConfigPanelSizer.Add( mainButtonsSizer, 0, wx.EXPAND, 5 )

		self.m_scrolledWindow1 = wx.ScrolledWindow( self.mainConfigPanel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.BORDER_THEME|wx.HSCROLL|wx.VSCROLL )
		self.m_scrolledWindow1.SetScrollRate( 5, 5 )
		mainConfigPanelSizer.Add( self.m_scrolledWindow1, 1, wx.EXPAND |wx.ALL, 5 )


		self.mainConfigPanel.SetSizer( mainConfigPanelSizer )
		self.mainConfigPanel.Layout()
		mainConfigPanelSizer.Fit( self.mainConfigPanel )
		self.m_notebook3.AddPage( self.mainConfigPanel, u"Main", False )
		self.systemsConfigPanel = wx.Panel( self.m_notebook3, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		systemsConfigPanelSizer = wx.BoxSizer( wx.VERTICAL )

		systemsButtonsSizer = wx.BoxSizer( wx.HORIZONTAL )

		self.systemsSaveButton = wx.Button( self.systemsConfigPanel, wx.ID_ANY, u"Save", wx.DefaultPosition, wx.DefaultSize, 0 )
		systemsButtonsSizer.Add( self.systemsSaveButton, 0, wx.ALL, 5 )

		self.systemsRevertButton = wx.Button( self.systemsConfigPanel, wx.ID_ANY, u"Revert", wx.DefaultPosition, wx.DefaultSize, 0 )
		systemsButtonsSizer.Add( self.systemsRevertButton, 0, wx.ALL, 5 )


		systemsConfigPanelSizer.Add( systemsButtonsSizer, 0, wx.EXPAND, 5 )

		self.m_scrolledWindow11 = wx.ScrolledWindow( self.systemsConfigPanel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.BORDER_THEME|wx.HSCROLL|wx.VSCROLL )
		self.m_scrolledWindow11.SetScrollRate( 5, 5 )
		systemsConfigPanelSizer.Add( self.m_scrolledWindow11, 1, wx.EXPAND |wx.ALL, 5 )


		self.systemsConfigPanel.SetSizer( systemsConfigPanelSizer )
		self.systemsConfigPanel.Layout()
		systemsConfigPanelSizer.Fit( self.systemsConfigPanel )
		self.m_notebook3.AddPage( self.systemsConfigPanel, u"Systems", True )
		self.ignoredDirsPanel = wx.Panel( self.m_notebook3, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		ignoredDirsPanelSizer = wx.BoxSizer( wx.VERTICAL )

		ignoredDirsSaveRevertButtonSizer = wx.BoxSizer( wx.HORIZONTAL )

		self.ignoredDirsSaveButton = wx.Button( self.ignoredDirsPanel, wx.ID_ANY, u"Save", wx.DefaultPosition, wx.DefaultSize, 0 )
		ignoredDirsSaveRevertButtonSizer.Add( self.ignoredDirsSaveButton, 0, wx.ALL, 5 )

		self.ignoredDirsRevertButton = wx.Button( self.ignoredDirsPanel, wx.ID_ANY, u"Revert", wx.DefaultPosition, wx.DefaultSize, 0 )
		ignoredDirsSaveRevertButtonSizer.Add( self.ignoredDirsRevertButton, 0, wx.ALL, 5 )


		ignoredDirsPanelSizer.Add( ignoredDirsSaveRevertButtonSizer, 0, wx.EXPAND, 5 )

		ignoredDirsEditorSizer = wx.BoxSizer( wx.HORIZONTAL )

		m_listBox1Choices = []
		self.m_listBox1 = wx.ListBox( self.ignoredDirsPanel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, m_listBox1Choices, 0 )
		ignoredDirsEditorSizer.Add( self.m_listBox1, 1, wx.ALL|wx.EXPAND, 5 )

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
		self.m_notebook3.AddPage( self.ignoredDirsPanel, u"Ignored Directories", False )

		bSizer2.Add( self.m_notebook3, 1, wx.ALL|wx.EXPAND, 5 )

		buttonsSizer = wx.BoxSizer( wx.HORIZONTAL )

		self.okButton = wx.Button( self, wx.ID_ANY, u"Go!", wx.DefaultPosition, wx.DefaultSize, 0 )
		buttonsSizer.Add( self.okButton, 0, wx.ALIGN_BOTTOM|wx.ALL|wx.BOTTOM, 5 )

		self.exitButton = wx.Button( self, wx.ID_ANY, u"Exit", wx.DefaultPosition, wx.DefaultSize, 0 )
		buttonsSizer.Add( self.exitButton, 0, wx.ALIGN_BOTTOM|wx.ALL, 5 )


		bSizer2.Add( buttonsSizer, 0, wx.ALIGN_BOTTOM|wx.BOTTOM|wx.SHAPED, 5 )


		self.SetSizer( bSizer2 )
		self.Layout()

		self.Centre( wx.BOTH )

	def __del__( self ):
		pass


