# -*- coding: utf-8 -*-

"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

"""
L'adresse à géocoder est fournis par une expression. Cette expression peut faire référence à une colonne ou concatener plusieurs colonne.
Il est possible de restreindre la recherche à un code INSEE.
Les algo "Geocodage" et "Geocodage inverse" peuvent être utilisées
"""
__author__ = 'JB Desbas - Quartier libre'
__date__ = '2018-08-27'
__copyright__ = '(C) 2018 by JB Desbas - Quartier libre'

from PyQt5.QtCore import QCoreApplication,QVariant
from qgis.core import (QgsProcessing,QgsProject,QgsPointXY,QgsGeometry,QgsWkbTypes,
                       QgsFeatureSink,QgsField,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterVectorLayer,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterExpression,
                       QgsCoordinateTransform,QgsCoordinateReferenceSystem,
                       QgsExpression,QgsExpressionContext,QgsExpressionContextScope)
import processing
from time import sleep

import requests
def geocode(query,citycode=None):
    base_url='https://api-adresse.data.gouv.fr/search/'
    limit=1
    autocomplete=0
    payload={'q':query,'limit':limit,'autocomplete':autocomplete,'citycode':citycode}
    r = requests.get(base_url,payload)
    if r.status_code!=200 or len(r.json().get('features'))<1:
        return False
    return r.json().get('features')[0]

class Geocode(QgsProcessingAlgorithm):
    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'
    INSEE_COM = 'INSEE_COM'
    ADRESSE = 'ADRESSE'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return Geocode()

    def name(self):
        return 'geocode'

    def displayName(self):
        return self.tr('Géocodage')

    def group(self):
        return self.groupId()

    def groupId(self):
        return 'geocode'

    def shortHelpString(self):
        return self.tr(
        """Récupérer les coordonnées géographiques d'une adresse depuis la BAN grâce à l'API adresse.data.gouv.fr
        <p>L'algorithm limite automatiquement le nombre de requêtes à 10/secondes (limitation de l'API).
        <p>Il est possible de spécifier le code INSEE d'une adresse.
        <dl><h3>Champs retournés</h3>
        <dt>ban_label</dt>
        <dd>Adresse trouvée dans la BAN</dd>
        <dt>ban_citycode</dt>
        <dd>Code INSEE de la commune</dd>
        <dt>ban_score</dt>
        <dd>Le score de correspondance ([0 à 1])</dd>
        <dt>ban_type</dt>
        <dd>La precision du points (housnumber > street > municipality)</dd>
        
        </dl>
        """)

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Input layer'),
                [QgsProcessing.TypeVector]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterExpression(
                self.ADRESSE,
                self.tr('Adresse'),
                defaultValue="NULL",
                parentLayerParameterName=self.INPUT,
                optional=False
            )
        )
        
        self.addParameter(
            QgsProcessingParameterExpression(
                self.INSEE_COM,
                self.tr('Code Insee'),
                defaultValue="NULL",
                parentLayerParameterName=self.INPUT,
                optional=True
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Géocodage'),
                QgsProcessing.TypeVectorPoint
            )
        )

    def processAlgorithm(self, parameters, context, feedback):

        source = self.parameterAsSource(
            parameters,
            self.INPUT,
            context
        )
        insee_com = self.parameterAsExpression(
            parameters,
            self.INSEE_COM,
            context
        )
        adresse = self.parameterAsExpression(
            parameters,
            self.ADRESSE,
            context
        )

        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))

        fields=source.fields()
        fields.append(QgsField('ban_label',QVariant.String,len=6)) or feedback.reportError('Le champs ban_label existe deja, son contenu sera remplacé')
        fields.append(QgsField('ban_citycode',QVariant.String,len=100)) or feedback.reportError('Le champs ban_citycode existe deja, son contenu sera remplacé')
        fields.append(QgsField('ban_score',QVariant.Double,len=10,prec=5)) or feedback.reportError('Le champs ban_score existe deja, son contenu sera remplacé')
        fields.append(QgsField('ban_type',QVariant.String,len=20)) or feedback.reportError('Le champs ban_type existe deja, son contenu sera remplacé')
     
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            fields,
            QgsWkbTypes.Point,
            QgsCoordinateReferenceSystem(2154)
        )

        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        total = 100.0 / source.featureCount() if source.featureCount() else 0
        features = source.getFeatures()

        citycode_expr=QgsExpression(insee_com)
        adresse_expr=QgsExpression(adresse)
        context = self.createExpressionContext(parameters, context, source)
        scope = QgsExpressionContextScope()
        citycode_expr.prepare(context)
        adresse_expr.prepare(context)
        for current, feature in enumerate(features):
            if feedback.isCanceled():
                break
            
            scope.setFeature(feature)
            context.appendScope(scope)
            citycode=citycode_expr.evaluate(context)           
            adresse=adresse_expr.evaluate(context)
            
            response = geocode(adresse,citycode=citycode)
            if response :
                #feedback.pushDebugInfo(str(response['properties'].get('score')))
                attr=feature.attributes()
                for i in range(fields.count()-len(attr)):
                    attr.append(None)
                feature.setFields(fields)
                feature.setAttributes(attr)
                feature.setAttribute('ban_label',response['properties'].get('label',''))
                feature.setAttribute('ban_citycode',response['properties'].get('citycode',''))
                feature.setAttribute('ban_score',response['properties'].get('score',''))
                feature.setAttribute('ban_type',response['properties'].get('type',''))

                x=response['properties'].get('x')
                y=response['properties'].get('y')
                #feature.setAttributes(attr)
                geom=QgsGeometry().fromPointXY(QgsPointXY(x,y))
                #t=QgsCoordinateTransform(QgsCoordinateReferenceSystem(2154),source.sourceCrs(),QgsProject.instance())
                #geom.transform(t)
                feature.setGeometry(geom)
            
            # Add a feature in the sink
            sink.addFeature(feature, QgsFeatureSink.FastInsert)

            # Update the progress bar
            feedback.setProgress(int(current * total))
            sleep(0.11)

        return {self.OUTPUT: dest_id}
