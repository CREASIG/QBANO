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
__author__ = 'JB Desbas - Quartier libre'
__date__ = '2018-08-27'
__copyright__ = '(C) 2018 by JB Desbas - Quartier libre'

from PyQt5.QtCore import QCoreApplication,QVariant
from qgis.core import (QgsProcessing,QgsProject,
                       QgsFeatureSink,QgsField,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsCoordinateTransform,QgsCoordinateReferenceSystem)
import processing
from time import sleep

import requests
def reverse_geocode(lon,lat):
    base_url='https://api-adresse.data.gouv.fr/reverse/'
    url='{}?lon={}&lat={}'.format(base_url,lon,lat)
    print(url)
    r = requests.get(url)
    if r.status_code!=200 or len(r.json().get('features'))<1:
        return False
    return r.json().get('features')[0]

def reverse_geocode_commune(lon,lat):
    base_url="https://geo.api.gouv.fr/communes"
    url='{}?lon={}&lat={}'.format(base_url,lon,lat)
    r = requests.get(url)
    if r.status_code!=200 or len(r.json())<1:
        return False
    return r.json()[0]

class ReverseGeocode(QgsProcessingAlgorithm):

    INPUT = 'INPUT'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ReverseGeocode()

    def name(self):
        return 'reversegeocode'

    def displayName(self):
        return self.tr('Géocodage inverse')

    def group(self):
        return self.groupId()

    def groupId(self):
        return 'geocode'

    def shortHelpString(self):
        return self.tr(
        """Retrouver l'adresse du point depuis la BAN grâce à l'API adresse.data.gouv.fr
        <p>Le script limite automatiquement le nombre de requêtes à 10/secondes (limitation de l'API).
        """)

    def initAlgorithm(self, config=None):

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Input layer'),
                [QgsProcessing.TypeVectorPoint]
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.OUTPUT,
                self.tr('Géocodage inverse'),
                QgsProcessing.TypeVectorPoint
            )
        )

    def processAlgorithm(self, parameters, context, feedback):

        source = self.parameterAsSource(
            parameters,
            self.INPUT,
            context
        )

        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))

        fields=source.fields()
        fields.append(QgsField('com_insee',QVariant.String,len=6))
        fields.append(QgsField('com_name',QVariant.String,len=100))
        fields.append(QgsField('street',QVariant.String,len=100))
        fields.append(QgsField('housenumber',QVariant.String,len=10))
        #fields.append(QgsField('addr_score',QVariant.Double,len=10,prec=2))
        
        (sink, dest_id) = self.parameterAsSink(
            parameters,
            self.OUTPUT,
            context,
            fields,
            source.wkbType(),
            source.sourceCrs()
        )

        if sink is None:
            raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        total = 100.0 / source.featureCount() if source.featureCount() else 0
        features = source.getFeatures()

        for current, feature in enumerate(features):
            if feedback.isCanceled():
                break
            geom=feature.geometry()
            t=QgsCoordinateTransform(source.sourceCrs(),QgsCoordinateReferenceSystem(4326),QgsProject.instance())
            geom.transform(t)
            response = reverse_geocode(geom.asPoint().x(),geom.asPoint().y())
            if response :
                #feedback.pushDebugInfo(str(response['properties'].get('score')))
                attr=feature.attributes()
                attr.append(response['properties'].get('citycode',''))
                attr.append(response['properties'].get('city',''))
                attr.append(response['properties'].get('street',''))
                attr.append(response['properties'].get('housenumber',''))
                #attr.append(response['properties'].get('score',None))
                feature.setFields(fields)
                feature.setAttributes(attr)
            else : #pas de retour, on geocode à la commune
                response=reverse_geocode_commune(geom.asPoint().x(),geom.asPoint().y())
                attr=feature.attributes()
                attr.append(response.get('code',''))
                attr.append(response.get('nom',''))
                attr.append('')
                attr.append('')
                #attr.append(response['properties'].get('score',None))
                feature.setFields(fields)
                feature.setAttributes(attr)
            # Add a feature in the sink
            sink.addFeature(feature, QgsFeatureSink.FastInsert)

            # Update the progress bar
            feedback.setProgress(int(current * total))
            sleep(0.11)

        return {self.OUTPUT: dest_id}
