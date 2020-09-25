from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QLineEdit, QLabel, QComboBox, QPushButton, QVBoxLayout, QDialog, \
    QDialogButtonBox

from aas.model.aas import *
from aas.model.base import *
from aas.model.concept import *
from aas.model.provider import *
from aas.model.submodel import *

from aas_editor.qt_models import Package


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
        self.layout = QtWidgets.QGridLayout(self)
        self.layout.addWidget(self.buttonBox, 10, 0, 1, 2)
        self.setLayout(self.layout)

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


class AddPackDialog(AddDialog):
    def __init__(self, parent=None):
        AddDialog.__init__(self, parent, "Add Package")
        self.nameLabel = QLabel("&Package name:", self)
        self.nameLineEdit = QLineEdit(self)
        self.nameLabel.setBuddy(self.nameLineEdit)

        self.nameLineEdit.textChanged.connect(self.validate)
        self.nameLineEdit.setFocus()
        self.layout.addWidget(self.nameLabel, 0, 0)
        self.layout.addWidget(self.nameLineEdit, 0, 1)

    def validate(self, nameText):
        self.buttonOk.setEnabled(True) if nameText else self.buttonOk.setDisabled(True)

    @checkIfAccepted
    def getObj2add(self):
        return Package(name=self.nameLineEdit.text())


class AddAssetDialog(AddDialog):
    def __init__(self, parent=None, defaultKind=AssetKind.INSTANCE,
                 defaultIdType=IdentifierType.IRI, defaultId=""):
        AddDialog.__init__(self, parent, "Add asset")
        self.kindLabel = QLabel("&Kind:", self)
        self.kindComboBox = QComboBox(self)
        self.kindLabel.setBuddy(self.kindComboBox)
        items = [str(member) for member in type(defaultKind)]
        self.kindComboBox.addItems(items)
        self.kindComboBox.setCurrentText(str(defaultKind))

        self.idTypeLabel = QLabel("id_&type:", self)
        self.idTypeComboBox = QComboBox(self)
        self.idTypeLabel.setBuddy(self.idTypeComboBox)
        items = [str(member) for member in type(defaultIdType)]
        self.idTypeComboBox.addItems(items)
        self.idTypeComboBox.setCurrentText(str(defaultIdType))

        self.idLabel = QLabel("&id:", self)
        self.idLineEdit = QLineEdit(defaultId, self)
        self.idLabel.setBuddy(self.idLineEdit)
        self.idLineEdit.textChanged.connect(self.validate)
        self.idLineEdit.setFocus()

        self.layout.addWidget(self.kindLabel, 0, 0)
        self.layout.addWidget(self.kindComboBox, 0, 1)
        self.layout.addWidget(self.idTypeLabel, 1, 0)
        self.layout.addWidget(self.idTypeComboBox, 1, 1)
        self.layout.addWidget(self.idLabel, 2, 0)
        self.layout.addWidget(self.idLineEdit, 2, 1)

    def validate(self, nameText):
        self.buttonOk.setEnabled(True) if nameText else self.buttonOk.setDisabled(True)

    @checkIfAccepted
    def getObj2add(self):
        kind = eval(self.kindComboBox.currentText())
        ident = Identifier(self.idLineEdit.text(), eval(self.idTypeComboBox.currentText()))
        return Asset(kind, ident)


class AddShellDialog(AddDialog):
    def __init__(self, parent=None, defaultIdType=base.IdentifierType.IRI, defaultId="", assetsToChoose=None):
        AddDialog.__init__(self, parent)
        self.setWindowTitle("Add shell")

        self.idTypeLabel = QLabel("id_type:", self)
        self.idTypeComboBox = QComboBox(self)
        items = [str(member) for member in type(defaultIdType)]
        self.idTypeComboBox.addItems(items)
        self.idTypeComboBox.setCurrentText(str(defaultIdType))

        self.idLabel = QLabel("id:", self)
        self.idLineEdit = QLineEdit(defaultId, self)
        self.idLineEdit.textChanged.connect(self.validate)
        self.idLineEdit.setFocus()

        self.assetLabel = QLabel("Asset:", self)
        self.assetComboBox = QComboBox(self)
        self.assetComboBox.addItems(assetsToChoose)

        self.layout.addWidget(self.idTypeLabel, 0, 0)
        self.layout.addWidget(self.idTypeComboBox, 0, 1)
        self.layout.addWidget(self.idLabel, 1, 0)
        self.layout.addWidget(self.idLineEdit, 1, 1)
        self.layout.addWidget(self.assetLabel, 2, 0)
        self.layout.addWidget(self.assetComboBox, 2, 1)

    def validate(self, nameText):
        if nameText:
            self.buttonOk.setDisabled(False)
        else:
            self.buttonOk.setDisabled(True)


class AddDescriptionDialog(AddDialog):
    def __init__(self, parent=None, defaultLang=""):
        AddDialog.__init__(self, parent)
        self.setWindowTitle("Add description")

        self.langLabel = QLabel("language:", self)
        self.langLineEdit = QLineEdit(defaultLang, self)
        self.langLineEdit.textChanged.connect(self.validate)

        self.descrLabel = QLabel("description:", self)
        self.descrLineEdit = QLineEdit(self)
        self.descrLineEdit.textChanged.connect(self.validate)

        self.layout.addWidget(self.langLabel, 0, 0)
        self.layout.addWidget(self.langLineEdit, 0, 1)
        self.layout.addWidget(self.descrLabel, 1, 0)
        self.layout.addWidget(self.descrLineEdit, 1, 1)

    def validate(self):
        if self.langLineEdit.text() and self.descrLineEdit.text():
            self.buttonOk.setDisabled(False)
        else:
            self.buttonOk.setDisabled(True)
