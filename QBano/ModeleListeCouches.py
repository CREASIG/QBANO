from PyQt5 import *
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QDialog
from qgis.core import *
     
class ModeleListeCouches(QtCore.QAbstractTableModel):
    def __init__(self,data, parent=None, *args):
        QtCore.QAbstractTableModel.__init__(self, parent, *args)
        self.data = data
        
    def columnCount(self, parent):
        return 1
    
    def rowCount(self, parent):
        return len(self.data)
    
    def flags (self, index):
         return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsSelectable
     
    def headerData(self, col, orientation, role):
        return "Nom de la couche"
    
    def data(self, index, role):
        if index.isValid():
            if role == QtCore.Qt.CheckStateRole:
                if self.data[index.row()].isChecked():
                    return QtCore.Qt.Checked
                else:
                    return QtCore.Qt.Unchecked
            elif role == QtCore.Qt.FontRole:
                font = QtGui.QFont()
                if self.data[index.row()].isChecked():
                    font.setBold(True)
                else:
                    font.setBold(False)
                    return font
            elif role == QtCore.Qt.DisplayRole:
                return self.data[index.row()].text()
            return None 
    
    def setData (self, index, value, role):
        if index.isValid() and role == QtCore.Qt.CheckStateRole:
            if value == QtCore.Qt.Checked:
                self.data[index.row()].setChecked(True)
            else:
                self.data[index.row()].setChecked(False)
        self.dataChanged.emit(index, index)
        return True

    def getDonnees(self):
        return self.data
    
    
    
    

