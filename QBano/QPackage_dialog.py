# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QPackageDialog
                                 A QGIS plugin
 Port of builder to python3
                             -------------------
        begin                : 2017-10-04
        git sha              : $Format:%H$
        copyright            : (C) 2017 by CREASIG
        email                : gsherman@geoapt.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from PyQt5 import *
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import uic
from PyQt5.QtWidgets import *
import os
import codecs
from qgis.core import *
from xml.dom.minidom import parse, parseString

from .ModeleListeCouches import ModeleListeCouches


FORM_CLASS, _ = uic.loadUiType(os.path.join(
                               os.path.dirname(__file__), 'QPackage_dialog_base.ui'))

class QPackageDialog(QDialog, FORM_CLASS):
    def __init__(self,iface, parent=None):
        self.iface = iface
        """Constructor."""
        super(QPackageDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        #QgsMessageLog.logMessage("debut")
        
        
    # Choose the destination directory
    def chercherRepertoire(self):
        filename = QtWidgets.QFileDialog.getExistingDirectory(parent=None, caption=QtWidgets.QApplication.translate("select destination", "Select directory to Fling from..."), directory=QtCore.QDir.currentPath())
        if filename:
            self._repertoire.setText(filename)
            
        
    # Load layers of the current project
    def chargerCouches(self):
        # add the mains projections used by the user
        self._listeprojections.clear()
        self._listeprojections.addItem(QtWidgets.QApplication.translate("select crs", "- Select CRS -"))
        if QtCore.QSettings().value('UI/recentProjectionsAuthId') != None:
            for e in QtCore.QSettings().value('UI/recentProjectionsAuthId'):
                self._listeprojections.addItem(e + ' - ' + str(QgsCoordinateReferenceSystem(e).description()), e)
                
        
        # Add layers to the list
        # The vector layers are selected by default
        #layers = QgsProject.instance().mapLayers()
        data = []
        
        for nom in QgsProject.instance().mapLayers():
            layer = QgsProject.instance().mapLayer(nom)
            casecocher = QtWidgets.QCheckBox(layer.name())
            if(layer.type() == QgsMapLayer.VectorLayer):
                casecocher.setChecked(True)
        #    QgsMessageLog.logMessage(casecocher)
            data.append(casecocher)
        self._tableau.setModel(ModeleListeCouches(data))
         
    def copierCouches(self):
        # Save the current project
        QgsProject.instance().write();
        model = self._tableau.model()
        data = []
        layers = QgsProject.instance().mapLayers()
        
        #Initialise the progress bar and the steps 
        self._progression.setValue(0)
        nbrecouches = 0;
        for row in model.getDonnees():
            if(row.isChecked()):
                nbrecouches += 1
        pas = float(100 / nbrecouches)
        progression = float(0)
        messageerreuraffiche = False
        
        # manage the layers selected
        for row in model.getDonnees():
            if(row.isChecked()):
             
                for name in QgsProject.instance().mapLayers():
                    layer = QgsProject.instance().mapLayer(name)
                    if(layer.name() == row.text()):
                        # If the layer is a vector
                        if layer.type() == QgsMapLayer.VectorLayer:
                            layer.__class__ = QgsVectorLayer
                            if(self._repertoire != ""):
                            #load the destination projection. if the selected item of the gui list is empty, we use the layer's one
                                projection = layer.crs().authid()
                                if self._listeprojections.currentText() != QtWidgets.QApplication.translate("select crs", "- Select CRS -"):
                                    projection = self._listeprojections.itemData(self._listeprojections.currentIndex())
                            # write the qgis layer to the destination directory
                                if os.name == 'nt':
                                    QgsVectorFileWriter.writeAsVectorFormat(layer, self._repertoire.text() + "\\" + layer.name()  + ".shp", "utf-8", QgsCoordinateReferenceSystem(projection), "ESRI Shapefile")
                                else:
                                    QgsVectorFileWriter.writeAsVectorFormat(layer, self._repertoire.text() + "/" + layer.name()  + ".shp", "utf-8", QgsCoordinateReferenceSystem(projection), "ESRI Shapefile")
                               
                            # Change the projections of the layer in the project
                                layer.setCrs(QgsCoordinateReferenceSystem(projection));
                                progression += float(pas)
                                self._progression.setValue(progression)
                            else:
                            # Error message if no directory has been selected
                                if (False == messageerreuraffiche):
                                    QMessageBox.critical(self, QtWidgets.QApplication.translate("QPackage", "QPackage"), QtWidgets.QApplication.translate("choosedestination", "You must choose the destination directory"), QMessageBox.Ok);
                                    messageerreuraffiche = True
                                   
                    #if the layer is a raster, the plugin must copy the file
                        elif layer.type() == QgsMapLayer.RasterLayer:
                            layer.__class__ = QgsRasterLayer
                            if(self._repertoire.toPlainText() != ""):
                                if os.name == 'nt':
                                    shutil.copy2(layer.publicSource(), self._repertoire.toPlainText() + "\\" + os.path.basename(layer.publicSource()))
                                else:
                                    shutil.copy2(layer.publicSource(), self._repertoire.toPlainText() + "/" + os.path.basename(layer.publicSource()))
                                
                                progression += float(pas)
                                self._progression.setValue(progression)
                            else:
                                if (False == messageerreuraffiche):
                                    QMessageBox.critical(self, QtWidgets.QApplication.translate("QPackage", "QPackage"), QtWidgets.QApplication.translate("choosedestination", "You must choose the destination directory"), QMessageBox.Ok);
                                    messageerreuraffiche = True
                            
        if messageerreuraffiche == False: 
            # Change current project CRS before saving it
            srcCrs = self.iface.mapCanvas().mapSettings().destinationCrs()
            dstCrs = QgsCoordinateReferenceSystem(projection)
            self.iface.mapCanvas().setDestinationCrs(dstCrs)
            ext = self.iface.mapCanvas().extent()
            #trCrs = QgsCoordinateTransform(srcCrs, dstCrs)
            #self.iface.mapCanvas().setExtent(trCrs.transformBoundingBox(ext))
            
            # if no error
            if os.name == 'nt':
                fichierprojet = self._repertoire.text() + "\\" + (os.path.basename(QgsProject.instance().fileName()))
            else:
                fichierprojet = self._repertoire.text() + "/" + (os.path.basename(QgsProject.instance().fileName()))
            #if the project exist we save it to a new directory
            QgsMessageLog.logMessage(QgsProject.instance().fileName())
            if not os.path.isfile(QgsProject.instance().fileName()):
                if self._projectname.text() != "":
                    strproject = self._projectname.text()
                    if strproject[-4:] == ".qgs":
                        fichierprojet = self._repertoire.text() + "\\" + strproject
                    else:
                        fichierprojet = self._repertoire.text() + "\\" + strproject + ".qgs"
                else:
                    fichierprojet = self._repertoire.text() + "\\project.qgs"
                QgsMessageLog.logMessage(fichierprojet)
            # Save the project to the new directory
            QgsProject.instance().write(fichierprojet)
            # we change the path of the layers
            DOMTree = parse(fichierprojet)
            collection = DOMTree.documentElement
            maplayers = collection.getElementsByTagName("maplayer")
            #logging.basicConfig(filename='myapp.log', level=logging.INFO)
            #logging.info( "coucou")

            for row in model.getDonnees():
                if row.isChecked():
                    for name in QgsProject.instance().mapLayers():
                        layer = QgsProject.instance().mapLayer(name)
                        if(layer.name() == row.text()):
                            if(self._repertoire.text() != ""):
                                if layer.type() == QgsMapLayer.VectorLayer:
                                    #head, tail = os.path.split(layer.source())
                                    for coucheprojet in maplayers:
                                        coucheprojetnom = coucheprojet.getElementsByTagName('layername')[0].childNodes[0].data
                                        if coucheprojetnom == layer.name():
                                            projection = layer.crs().authid()
                                            if self._listeprojections.currentText() != "":
                                                projection = self._listeprojections.currentText()

                                            replaceText(coucheprojet.getElementsByTagName('datasource')[0], "./"+layer.name()  + ".shp")
                                            replaceText(coucheprojet.getElementsByTagName('provider')[0], "ogr")
                                            pr = "<spatialrefsys>"
                                            pr = pr + "<proj4>" + str(QgsCoordinateReferenceSystem(projection).toProj4()) + "</proj4>"
                                            pr = pr + "<srsid>" + str(QgsCoordinateReferenceSystem(projection).srsid()) + "</srsid>"
                                            pr = pr + "<srid>" + str(QgsCoordinateReferenceSystem(projection).postgisSrid()) + "</srid>"
                                            pr = pr + "<epsg>" + str(QgsCoordinateReferenceSystem(projection).authid()) + "</epsg>"
                                            pr = pr + "<description>" + str(QgsCoordinateReferenceSystem(projection).description()) + "</description>"
                                            pr = pr + "<projectionacronym>" + str(QgsCoordinateReferenceSystem(projection).projectionAcronym()) + "</projectionacronym>"
                                            pr = pr + "<ellipsoidacronym>" + str(QgsCoordinateReferenceSystem(projection).ellipsoidAcronym()) + "</ellipsoidacronym>"
                                            pr = pr + "</spatialrefsys>"
                                            #logging.info( pr)
                                            coucheprojet.getElementsByTagName('srs')[0] = pr

                                elif layer.type() == QgsMapLayer.RasterLayer:
                                    for coucheprojet in maplayers:
                                        coucheprojetnom = coucheprojet.getElementsByTagName('layername')[0].childNodes[0].data
                                        if coucheprojetnom == layer.name():
                                            replaceText(coucheprojet.getElementsByTagName('datasource')[0], os.path.basename(layer.publicSource()))
            file_handle = codecs.open(fichierprojet, "w", encoding="utf_8")
            #logging.info(DOMTree.toxml())
            file_handle.write(DOMTree.toxml())
            file_handle.close()
            self._progression.setValue(100)
            QMessageBox.warning(self, QApplication.translate("QPackage", "QPackage"), QApplication.translate("mustclose", "You must close Qgis to take into account changes"));





def replaceText(node, newText):
    if node.firstChild.nodeType != node.TEXT_NODE:
        raise Exception("node does not contain text")

    node.firstChild.replaceWholeText(newText)

