#  Copyright (C) 2021  Igor Garmaev, garmaev@gmx.net
#
#  This program is made available under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
#  A copy of the GNU General Public License is available at http://www.gnu.org/licenses/
#
#  This program is made available under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
#  A copy of the GNU General Public License is available at http://www.gnu.org/licenses/

from typing import Any

from PyQt5.QtCore import QModelIndex, Qt, QVariant, QPersistentModelIndex
from PyQt5.QtGui import QFont

from aas_editor.models import StandardTable, SetDataItem
from aas_editor.package import Package
from aas_editor.settings.app_settings import PACKAGE_ROLE, DEFAULT_FONT, OPENED_PACKS_ROLE, OPENED_FILES_ROLE, \
    DEFAULT_COLUMNS_IN_PACKS_TABLE, OBJECT_ROLE, COLUMN_NAME_ROLE, DATA_CHANGE_FAILED_ROLE, ADD_ITEM_ROLE, UNDO_ROLE, \
    REDO_ROLE


class PacksTable(StandardTable):
    currFont = QFont(DEFAULT_FONT)

    def openedPacks(self):
        packs = set()
        for i in range(self.rowCount()):
            item = self.index(row=i)
            pack: Package = item.data(PACKAGE_ROLE)
            if pack:
                try:
                    packs.add(pack)
                except AttributeError:
                    continue
        return packs

    def openedFiles(self):
        files = set([pack.file for pack in self.openedPacks()])
        return files

    def data(self, index: QModelIndex, role: int = ...) -> Any:
        if role == Qt.ForegroundRole:
            return self._getFgColor(index)
        elif role == OPENED_PACKS_ROLE:
            return self.openedPacks()
        elif role == OPENED_FILES_ROLE:
            return self.openedFiles()
        else:
            return super(PacksTable, self).data(index, role)

    def setData(self, index: QModelIndex, value: Any, role: int = ...) -> bool:
        if isinstance(index, QPersistentModelIndex):
            index = QModelIndex(index)
        if not index.isValid() and role not in (Qt.FontRole, ADD_ITEM_ROLE, UNDO_ROLE, REDO_ROLE):
            return QVariant()
        elif role == Qt.EditRole and index.column() not in DEFAULT_COLUMNS_IN_PACKS_TABLE:  # TODO refactor
            try:
                value = None if str(value) == "None" else value

                parentObj = index.data(OBJECT_ROLE)
                objName = index.data(COLUMN_NAME_ROLE)
                oldValue = getattr(parentObj, objName)

                setattr(parentObj, objName, value)
                self.setChanged(index)
                self.dataChanged.emit(index, index)
                self.undo.append(SetDataItem(index=QPersistentModelIndex(index), value=oldValue, role=role))
                self.redo.clear()
                return True
            except Exception as e:
                self.lastErrorMsg = f"Error occurred while setting {self.objByIndex(index).objectName}: {e}"
                self.dataChanged.emit(index, index, [DATA_CHANGE_FAILED_ROLE])
                return False
        else:
            return super(PacksTable, self).setData(index, value, role)
