from typing import Any, Iterable, Union

from PyQt5.QtCore import QAbstractItemModel, QVariant, QModelIndex, Qt, pyqtSignal
from aas.model import DictObjectStore, Submodel, NamespaceSet, SubmodelElement

from aas_editor.models import OBJECT_ROLE, NAME_ROLE, Package, DetailedInfoItem, StandardItem, \
    ATTRIBUTE_COLUMN, VALUE_COLUMN, PackTreeViewItem


class StandardTable(QAbstractItemModel):
    valueChangeFailed = pyqtSignal(['QString'])

    def __init__(self, columns=("Item",), rootItem: StandardItem = None):
        super(StandardTable, self).__init__()
        self._rootItem = rootItem if rootItem else DetailedInfoItem(None, "", None)
        self._columns = columns

    def data(self, index, role):
        if not index.isValid():
            return QVariant()
        return self.objByIndex(index).data(role)

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()
        parentObj = self.objByIndex(parent)
        return self.createIndex(row, column, parentObj.children()[row])

    def parent(self, child: QModelIndex) -> QModelIndex:
        childObj = self.objByIndex(child)
        parentObj = childObj.parent()
        if parentObj == self._rootItem:
            return QModelIndex()
        grandParentObj = parentObj.parent()
        row = grandParentObj.children().index(parentObj)
        return self.createIndex(row, 0, parentObj)

    def rowCount(self, parent: QModelIndex = ...) -> int:
        return len(self.objByIndex(parent).children())

    def columnCount(self, parent: QModelIndex = ...) -> int:
        return len(self._columns)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = ...) -> Any:
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self._columns[section]

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.NoItemFlags

        if (index.column() == ATTRIBUTE_COLUMN and not isinstance(index.parent().data(OBJECT_ROLE), dict)) \
                or self.hasChildren(index):
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable

        return Qt.ItemIsEditable | Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def hasChildren(self, parent: QModelIndex = ...) -> bool:
        return True if self.rowCount(parent) else False

    def objByIndex(self, index: QModelIndex):
        if not index.isValid():
            return self._rootItem
        return index.internalPointer()

    def iterItems(self, parent: QModelIndex = QModelIndex()):
        def recurse(parent):
            for row in range(self.rowCount(parent)):
                childIndex = self.index(row, 0, parent)
                yield childIndex
                child = self.objByIndex(childIndex)
                if child.children():
                    yield from recurse(childIndex)

        yield from recurse(parent)

    def findItemByObj(self, obj): #todo redefine to match()
        for item in self.iterItems():
            print("Name:", item.data(NAME_ROLE))
            try:
                if item.data(OBJECT_ROLE) == obj:
                    return item
            except AttributeError:
                continue


    def addData(self, parent: QModelIndex, value: Iterable, role: int = ...) -> bool:
        """Add items to Iterable"""
        self.addItem1(value, parent)

    def addItem(self, obj: Union[Package, SubmodelElement, Iterable], parent: QModelIndex = QModelIndex()):
        # obj must be iterable if add to list, dict or set
        parentObj = self.objByIndex(parent).data(OBJECT_ROLE)
        if isinstance(parentObj, DictObjectStore):
            parentObj.add(obj)
        elif isinstance(parentObj, Submodel):
            parentObj.submodel_element.add(obj) # todo change if they make Submodel iterable
        elif isinstance(parentObj, list):
            parentObj.extend(obj)
        elif isinstance(parentObj, set) or isinstance(parentObj, dict):
            parentObj.update(obj)
        elif isinstance(obj, Package):
            self.beginInsertRows(parent, self.rowCount(parent), self.rowCount(parent))
            item = PackTreeViewItem(obj, objName=obj.name)
            item.setParent(self.objByIndex(QModelIndex()))
            self.endInsertRows()
            return True
        else:
            raise AttributeError("The Object could not be added")
        self.update(parent)
        return True

    def update(self, index: QModelIndex):
        if not index.isValid():
            return QVariant()
        if self.hasChildren(index):
            self.removeRows(0, self.rowCount(index), index)
        self.beginInsertRows(index, self.rowCount(index), self.rowCount(index))
        self.objByIndex(index).populate()
        self.endInsertRows()
        self.dataChanged.emit(index, index.child(self.rowCount(index), self.columnCount(index)))
        return True

    def setData(self, index: QModelIndex, value: Any, role: int = ...) -> bool:
        if not index.isValid() or not role == Qt.EditRole:
            return QVariant()
        try:
            if self.hasChildren(index):
                self.removeRows(0, self.rowCount(index), index)
            value = None if str(value) == "None" else value
            item = self.objByIndex(index)
            if isinstance(index.parent().data(OBJECT_ROLE), list):
                item.parentObj[index.row()] = value
                item.obj = index.parent().data(OBJECT_ROLE)[index.row()]
            elif isinstance(index.parent().data(OBJECT_ROLE), set):
                item.parentObj.remove(item.obj)
                item.parentObj.add(value)
                item.obj = value
            elif isinstance(index.parent().data(OBJECT_ROLE), dict):
                if index.column() == VALUE_COLUMN:
                    item.parentObj[item.objName] = value
                    item.obj = item.parentObj[item.objName]
                elif index.column() == ATTRIBUTE_COLUMN:
                    item.parentObj[value] = item.parentObj.pop(item.objName)
                    item.objName = value
            else:
                setattr(item.parentObj, item.objName, value)
                item.obj = getattr(item.parentObj, item.objName)
            if item.obj == value:
                item.populate()
                self.dataChanged.emit(index,
                                      index.child(self.rowCount(index), self.columnCount(index)))
                return True
            else:
                self.valueChangeFailed.emit(
                    f"{self.objByIndex(index).objectName} could not be changed to {value}")
        except (ValueError, AttributeError) as e:
            self.dataChanged.emit(index, index)
            self.valueChangeFailed.emit(
                f"Error occurred while setting {self.objByIndex(index).objName}: {e}")
        return False

    def removeRows(self, row: int, count: int, parent: QModelIndex = ...) -> bool:
        parentItem = self.objByIndex(parent)

        self.beginRemoveRows(parent, row, row+count-1)
        for n in range(count):
            child = parentItem.children()[row]
            child.setParent(None)
            # child.deleteLater()
        self.endRemoveRows()
        return True

    def clearRows(self, row: int, count: int, parent: QModelIndex = ..., defaultVal="Not given") -> bool:
        """Delete rows if they are children of Iterable else set to Default"""
        parentItem = self.objByIndex(parent)

        self.beginRemoveRows(parent, row, row+count-1)
        for n in range(row+count-1, row-1, -1):
            child = parentItem.children()[n]
            if isinstance(parentItem.obj, list):
                parentItem.obj.pop[n]
                child.setParent(None)
            elif isinstance(parentItem.obj, set):
                parentItem.obj.remove(child.obj)
                child.setParent(None)
            elif isinstance(parentItem.obj, dict):
                parentItem.obj.pop(child.objName)
                child.setParent(None)
            elif isinstance(parentItem.obj, (DictObjectStore, NamespaceSet)):
                parentItem.obj.discard(child.obj)
                child.setParent(None)
            else:
                if not defaultVal == "Not given":
                    self.setData(self.index(n, 0, parent), defaultVal, Qt.EditRole)
                else:
                    self.valueChangeFailed.emit(
                        f"{child.objectName} could not be deleted or set to default")
        self.endRemoveRows()
        self.dataChanged.emit(parent, parent.child(self.rowCount(parent), self.columnCount(parent)))
        return True

    def clearRow(self, row: int, parent: QModelIndex = ..., defaultVal="Not given") -> bool:
        """Delete row if it is child of Iterable else set to Default"""
        self.clearRows(row, 1, parent, defaultVal)
