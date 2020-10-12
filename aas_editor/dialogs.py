from typing import NamedTuple

from PyQt5.QtCore import Qt
from PyQt5 import QtWidgets
from PyQt5.QtGui import QIntValidator, QDoubleValidator
from PyQt5.QtWidgets import QLineEdit, QLabel, QComboBox, QPushButton, QDialog, QDialogButtonBox, \
    QGroupBox, QCheckBox

from aas.model.aas import *
from aas.model.base import *
from aas.model.concept import *
from aas.model.provider import *
from aas.model.submodel import *

from aas_editor.util import getReqParams4init, issubtype, inheritors, isMeta


class AddDialog(QDialog):
    """Base abstract class for custom dialogs for adding data"""

    def __init__(self, parent=None, windowTitle=""):
        QDialog.__init__(self, parent)
        self.setWindowTitle(windowTitle)
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.buttonOk = self.buttonBox.button(QDialogButtonBox.Ok)
        self.buttonOk.setDisabled(True)
        self.dialogLayout = QtWidgets.QVBoxLayout(self)
        self.dialogLayout.addWidget(self.buttonBox)
        self.setLayout(self.dialogLayout)

    def getObj2add(self):
        pass


def checkIfAccepted(func):
    """Decorator for checking if user clicked ok"""

    def wrap(addDialog):
        if addDialog.result() == QDialog.Accepted:
            return func(addDialog)
        else:
            raise ValueError("Adding was cancelled")

    return wrap


class DescrGroupBox(QGroupBox):
    def __init__(self, title, parent=None, defaultLang=""):
        super().__init__(title, parent)
        layout = QtWidgets.QGridLayout(self)

        self.langLabel = QLabel("&Language:", self)
        self.langLineEdit = QLineEdit(defaultLang, self)
        self.langLabel.setBuddy(self.langLineEdit)
        self.langLineEdit.setFocus()

        self.descrLabel = QLabel("&Description:", self)
        self.descrLineEdit = QLineEdit(self)
        self.descrLabel.setBuddy(self.descrLineEdit)

        layout.addWidget(self.langLabel, 0, 0)
        layout.addWidget(self.langLineEdit, 0, 1)
        layout.addWidget(self.descrLabel, 0, 2)
        layout.addWidget(self.descrLineEdit, 0, 3)
        self.setLayout(layout)


class AddDescriptionDialog(AddDialog):
    def __init__(self, parent=None, defaultLang=""):
        AddDialog.__init__(self, parent, "Add description")
        self.buttonOk.setEnabled(True)

        self.descrsLayout = QtWidgets.QGridLayout(self)
        self.dialogLayout.addLayout(self.descrsLayout, 0, 0)

        self.descrGroupBoxes = []
        self.addDescrField(defaultLang)

        plusDescr = QPushButton("+description", self)
        plusDescr.clicked.connect(self.addDescrField)
        self.dialogLayout.addWidget(plusDescr, 9, 0)

    def addDescrField(self, defaultLang):
        descrGroupBox = DescrGroupBox("", self, defaultLang=defaultLang)
        self.descrGroupBoxes.append(descrGroupBox)
        self.descrsLayout.addWidget(descrGroupBox)

    @checkIfAccepted
    def getObj2add(self):
        descrUpdateDict = {}
        for descrGroupBox in self.descrGroupBoxes:
            lang = descrGroupBox.langLineEdit.text()
            descr = descrGroupBox.descrLineEdit.text()
            if lang and descr:
                descrUpdateDict[lang] = descr
        return descrUpdateDict


def getInputWidget(objType, rmDefParams=True, objName="", attrsToHide: dict = None, parent=None) -> QtWidgets.QWidget:
    print(objType, objType.__str__, objType.__repr__, objType.__class__)
    attrsToHide = attrsToHide if attrsToHide else {}
    if isMeta(objType):
        objTypes = inheritors(objType)
        widget = TypeOptionObjGroupBox(objTypes, "", attrsToHide=attrsToHide,
                             rmDefParams=rmDefParams, objName=objName, parent=parent)
    elif issubtype(objType, (list, tuple, set, dict)) and not issubtype(objType, DictItem):# typing.Iterable):
        widget = IterableGroupBox(objType, "", rmDefParams=rmDefParams, parent=parent)
    elif issubtype(objType, Union):
        objTypes = objType.__args__
        widget = TypeOptionObjGroupBox(objTypes, "", attrsToHide=attrsToHide,
                             rmDefParams=rmDefParams, objName=objName, parent=parent)
    elif issubtype(objType, AASReference):
        if objType.__args__:
            type_ = objType.__args__[0]
            attrsToHide["type_"] = type_
        widget = ObjGroupBox(objType, "", attrsToHide=attrsToHide,
                             rmDefParams=rmDefParams, objName=objName, parent=parent)
    elif issubtype(objType, (bool, str, int, float, Enum, Type)):
        widget = StandardInputWidget(objType, parent=parent)
    else:
        widget = ObjGroupBox(objType, "", rmDefParams=rmDefParams, attrsToHide=attrsToHide,
                             objName=objName, parent=parent)
    return widget


class AddObjDialog(AddDialog):
    def __init__(self, objType, parent=None, rmDefParams=True, objName=""):
        objName = objName if objName else objType.__name__
        AddDialog.__init__(self, parent, f"Add {objName}")
        self.buttonOk.setEnabled(True)
        self.inputWidget = getInputWidget(objType, rmDefParams=rmDefParams, objName=objName)
        self.inputWidget.setObjectName("mainBox")
        self.inputWidget.setStyleSheet("#mainBox{border:0;}")
        self.dialogLayout.insertWidget(0, self.inputWidget)

    def getInputWidget(self):
        pass
    @checkIfAccepted
    def getObj2add(self):
        return self.inputWidget.getObj2add()


class GroupBox(QGroupBox):
    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.setAlignment(Qt.AlignLeft)
        self.setLayout(QtWidgets.QVBoxLayout(self))


class ObjGroupBox(GroupBox):
    def __init__(self, objType, title, parent=None, attrsToHide: dict = None, rmDefParams=True,
                 objName=""):
        super().__init__(title, parent)

        self.objType = objType
        self.attrsToHide = attrsToHide if attrsToHide else {}
        self.attrWidgetDict = {}

        reqAttrsDict = getReqParams4init(objType, rmDefParams, attrsToHide)

        if reqAttrsDict:
            for attr, attrType in reqAttrsDict.items():
                widgetLayout = self.getInputWidgetLayout(attr, attrType, rmDefParams)
                self.layout().addLayout(widgetLayout)
        else:
            widgetLayout = self.getInputWidgetLayout(objName, objType, rmDefParams)
            self.layout().addLayout(widgetLayout)

    def getInputWidgetLayout(self, attr, attrType, rmDefParams=True) -> QtWidgets.QHBoxLayout:
        print(f"Getting widget for attr: {attr} of type: {attrType}")
        layout = QtWidgets.QHBoxLayout()
        label = QLabel(f"{attr}:")
        widget = getInputWidget(attrType, rmDefParams=rmDefParams)
        self.attrWidgetDict[attr] = widget
        if isinstance(widget, QGroupBox):
            widget.setTitle(f"{attr}:")
        else:
            layout.addWidget(label)
        layout.addWidget(widget)
        return layout

    def getObj2add(self):
        attrValueDict = {}
        for attr, widget in self.attrWidgetDict.items():
            attrValueDict[attr] = widget.getObj2add()
        for attr, value in self.attrsToHide.items():
            attrValueDict[attr] = value
        obj = self.objType(**attrValueDict)
        return obj

DictItem = NamedTuple("DictItem", key=Any, value=Any)

class IterableGroupBox(GroupBox):
    def __init__(self, iterableType, title, parent=None, rmDefParams=True):
        super().__init__(title, parent)
        self.iterableType = iterableType
        self.argTypes = list(iterableType.__args__)
        plusButton = QPushButton(f"+ Element", self)
        plusButton.clicked.connect(self.addInputWidget)
        self.layout().addWidget(plusButton)
        self.inputWidgets = []
        self.addInputWidget(rmDefParams)

    def addInputWidget(self, rmDefParams):
        if ... in self.argTypes:
            self.argTypes.remove(...)

        if not issubtype(self.iterableType, dict):
            if len(self.argTypes) == 1:
                argType = self.argTypes[0]
            else:
                raise TypeError(f"expected 1 argument, got {len(self.argTypes)}", self.argTypes)
        else:
            if len(self.argTypes) == 2:
                DictItem._field_types["key"] = self.argTypes[0]
                DictItem._field_types["value"] = self.argTypes[1]
                argType = DictItem
            else:
                raise TypeError(f"expected 2 arguments, got {len(self.argTypes)}", self.argTypes)
        widget = getInputWidget(argType,
                                objName=f"{argType.__name__} {len(self.inputWidgets)}",
                                rmDefParams=rmDefParams)
        self.inputWidgets.append(widget)
        self.layout().insertWidget(self.layout().count()-1, widget)

    def getObj2add(self):
        listObj = []
        for widget in self.inputWidgets:
            listObj.append(widget.getObj2add())
        if issubtype(self.iterableType, tuple):
            obj = tuple(listObj)
        if issubtype(self.iterableType, list):
            obj = list(listObj)
        if issubtype(self.iterableType, set):
            obj = set(listObj)
        if issubtype(self.iterableType, dict):
            obj = dict(listObj)
        return obj


class StandardInputWidget(QtWidgets.QWidget):
    def __init__(self, attrType, parent=None):
        super(StandardInputWidget, self).__init__(parent)
        self.attrType = attrType
        self.widget = self._initWidget()
        widgetLayout = QtWidgets.QVBoxLayout(self)
        widgetLayout.addWidget(self.widget)
        self.setLayout(widgetLayout)

    def _initWidget(self):
        if issubtype(self.attrType, bool):
            widget = QCheckBox(self)
        elif issubtype(self.attrType, str):
            widget = QLineEdit(self)
        elif issubtype(self.attrType, int):
            widget = QLineEdit(self)
            widget.setValidator(QIntValidator())
        elif issubtype(self.attrType, float):
            widget = QLineEdit(self)
            widget.setValidator(QDoubleValidator())
        elif issubtype(self.attrType, Enum):
            widget = QComboBox(self)
            items = [member for member in self.attrType]
            for typ in items:
                widget.addItem(typ.name, typ)
        elif issubtype(self.attrType, Type):
            widget = QComboBox(self)
            union = self.attrType.__args__[0]
            if type(union) == TypeVar:
                baseType = union.__bound__
                types = inheritors(baseType)
            else:
                types = union.__args__
            for typ in types:
                widget.addItem(typ.__name__, typ)
        return widget

    def getObj2add(self):
        if issubtype(self.attrType, bool):
            obj = self.widget.isChecked()
        elif issubtype(self.attrType, str):
            obj = self.widget.text()
        elif issubtype(self.attrType, int):
            obj = int(self.widget.text())
        elif issubtype(self.attrType, float):
            obj = float(self.widget.text())
        elif issubtype(self.attrType, (Enum, Type)):
            obj = self.widget.currentData()
        return obj


class ChooseFromDialog(AddDialog):
    def __init__(self, objList, title, parent=None):
        super(ChooseFromDialog, self).__init__(parent, title)
        self.buttonOk.setEnabled(True)

        self.objComboBox = QComboBox(self)
        for obj in objList:
            self.objComboBox.addItem(str(obj), obj)
        self.dialogLayout.insertWidget(0, self.objComboBox)

    @checkIfAccepted
    def getObj2add(self):
        obj = self.objComboBox.currentData()
        return obj


class TypeOptionObjGroupBox(GroupBox): # todo reimplement when Datatypes Data, Duration, etc. are ready
    def __init__(self, objTypes, title, parent=None, attrsToHide: dict = None, rmDefParams=False, objName=""):
        super(TypeOptionObjGroupBox, self).__init__(title, parent)
        self.rmDefParams = rmDefParams
        self.attrsToHide = attrsToHide

        self.typeComboBox = QComboBox(self)
        for objType in objTypes:
            self.typeComboBox.addItem(objType.__name__, objType)
        self.layout().insertWidget(0, self.typeComboBox)

        currObjType = self.typeComboBox.currentData()
        self.widget = getInputWidget(currObjType, rmDefParams, attrsToHide=attrsToHide, parent=self)
        self.layout().addWidget(self.widget)

        self.typeComboBox.currentIndexChanged.connect(lambda i: self.replGroupBox(self.typeComboBox.itemData(i)))

    def replGroupBox(self, objType):
        newWidget = getInputWidget(objType, self.rmDefParams, attrsToHide=self.attrsToHide, parent=self)
        self.layout().replaceWidget(self.widget, newWidget)
        self.widget.close()
        newWidget.showMinimized()
        self.widget = newWidget
        self.window().adjustSize()

    def getObj2add(self):
        return self.widget.getObj2add()
