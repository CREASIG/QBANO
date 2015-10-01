# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QBano
                                 A QGIS plugin
 QBano
                             -------------------
        begin                : 2015-07-09
        copyright            : (C) 2015 by CREASIG
        email                : eric.creasig.fr
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load QBano class from file QBano.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from QBano import QBano
    return QBano(iface)
