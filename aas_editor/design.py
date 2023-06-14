# -*- coding: utf-8 -*-

#  Copyright (C) 2021  Igor Garmaev, garmaev@gmx.net
#
#  This program is made available under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
#  A copy of the GNU General Public License is available at http://www.gnu.org/licenses/

# Form implementation generated from reading ui file 'aas_editor/mainwindow_base.ui'
#
# Created by: PyQt5 UI code generator 5.15.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.
import typing

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QFrame, QWidget, QHBoxLayout

from aas_editor.models import PacksTable, StandardTable, PackTreeViewItem
from aas_editor.settings import EXTENDED_COLUMNS_IN_PACK_TABLE
from aas_editor.settings.app_settings import APPLICATION_NAME, TOOLBARS_HEIGHT, ATTRIBUTE_COLUMN, AppSettings, \
    DEFAULT_COLUMNS_IN_PACKS_TABLE
from aas_editor.widgets import ToolBar, TabWidget, SearchBar, PackTreeView


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setAutoFillBackground(True)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setContentsMargins(2, 0, 2, 0)

        self.splitter = QtWidgets.QSplitter(self.centralwidget)
        self.mainLayoutWidget = QtWidgets.QWidget(self.splitter)
        self.mainVerticalLayout = self.setupMainLayout(parent=self.mainLayoutWidget)

        self.packTreeModel = self.setupMainTreeModel()
        self.mainTreeView = self.setupMainTreeView(parent=self.mainLayoutWidget, model=self.packTreeModel)


        self.toolBar = ToolBar(self.mainLayoutWidget)
        self.searchBarPack = SearchBar(self.mainTreeView, filterColumns=[ATTRIBUTE_COLUMN],
                                       parent=self.mainLayoutWidget, closable=True)
        self.toolBarWidget = self.setupToolbar(widgetsInside=(self.toolBar, self.searchBarPack))

        self.mainVerticalLayout.addWidget(self.toolBarWidget)
        self.mainVerticalLayout.addWidget(self.mainTreeView)

        # Sub part
        self.subLayoutWidget = QtWidgets.QWidget(self.splitter)
        self.subVerticalLayout = self.setupSubLayout(parent=self.subLayoutWidget)

        self.splitterTabWidgets = QtWidgets.QSplitter(self.subLayoutWidget)
        self.splitterTabWidgets.setOrientation(QtCore.Qt.Horizontal)
        self.splitterTabWidgets.setFrameShape(QFrame.StyledPanel)
        self.subVerticalLayout.addWidget(self.splitterTabWidgets)

        self.mainTabWidget = TabWidget(self.splitterTabWidgets, unclosable=True)
        self.gridLayout.addWidget(self.splitter, 1, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)

        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(f"{APPLICATION_NAME}[*]")

    def setOrientation(self, o: QtCore.Qt.Orientation):
        if o == QtCore.Qt.Horizontal:
            self.splitter.setOrientation(QtCore.Qt.Horizontal)
            AppSettings.ORIENTATION.setValue(QtCore.Qt.Horizontal)
        elif o == QtCore.Qt.Vertical:
            self.splitter.setOrientation(QtCore.Qt.Vertical)
            AppSettings.ORIENTATION.setValue(QtCore.Qt.Vertical)

    def setupToolbar(self, widgetsInside: typing.Iterable):
        toolBarHLayout = QHBoxLayout()
        toolBarHLayout.setContentsMargins(0, 0, 0, 0)
        for widget in widgetsInside:
            toolBarHLayout.addWidget(widget)
        toolBarWidget = QWidget()
        toolBarWidget.setFixedHeight(TOOLBARS_HEIGHT)
        toolBarWidget.setLayout(toolBarHLayout)
        return toolBarWidget

    def setupMainTreeView(self, parent, model: StandardTable) -> PackTreeView:
        mainTreeView = PackTreeView(parent)
        mainTreeView.setFocusPolicy(QtCore.Qt.StrongFocus)
        mainTreeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        mainTreeView.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        mainTreeView.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        mainTreeView.setModelWithProxy(model)
        for column in range(model.columnCount(), 2, -1):
            mainTreeView.hideColumn(column)
        return mainTreeView

    def setupMainLayout(self, parent) -> QtWidgets.QVBoxLayout:
        mainVerticalLayout = QtWidgets.QVBoxLayout(parent)
        mainVerticalLayout.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        mainVerticalLayout.setContentsMargins(0, 0, 0, 0)
        mainVerticalLayout.setSpacing(5)
        return mainVerticalLayout

    def setupSubLayout(self, parent) -> QtWidgets.QVBoxLayout:
        subVerticalLayout = QtWidgets.QVBoxLayout(parent)
        subVerticalLayout.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        subVerticalLayout.setContentsMargins(0, 0, 0, 0)
        return subVerticalLayout

    def setupMainTreeModel(self) -> StandardTable:
        columns_in_packs_table = list(DEFAULT_COLUMNS_IN_PACKS_TABLE)
        columns_in_packs_table.extend(EXTENDED_COLUMNS_IN_PACK_TABLE)
        return PacksTable(columns_in_packs_table, PackTreeViewItem(None, None))
