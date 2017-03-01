#!/usr/bin/env python
"""\
Read dxf file
"""

# usage:

# import the necesary packages
import math
import dxfgrabber

dwg = dxfgrabber.readfile("400Afc-only.dxf")
print("DXF version: {}".format(dwg.dxfversion))

def distanceBetwenTwoPoints(start, end):

    d = math.sqrt( ( (end[0] - start[0] ) ** 2) + ( ( end[1] - start[1] ) ** 2 ) )
    return d

def distanceInX(start, end):
    d = math.sqrt( ( (end[0] - start[0] ) ** 2) + 0 )
    return d

def distanceInY(start, end):
    d = math.sqrt( 0 + ( ( end[1] - start[1] ) ** 2 ) )
    return d

def moveGrblX(distance):

    if(distance != 0):
        # print "G01 X%.2f" % distance
        return "G91 G0 X%.2f\n" % distance

    return ""

def moveGrblY(distance):

    if(distance != 0):
        # print "G01 Y%.2f" % distance
        return "G91 G0 Y%.2f\n" % distance
    
    return ""

# Global vars
allXCoordinates = []
allYCoordinates = []

machinePosition = [0, 0, 0]

commands = "G17 G20 G90 G94 G54\n"

# all_layer_0_entities = [entity for entity in dwg.entities if entity.layer == '0']

allLines = [entity for entity in dwg.entities if entity.dxftype == 'LINE']
for line in allLines:

    print "[INFO] LINE.Start X: %.2f Y: %.2f Z: %.2f\n" % (line.start[0], line.start[1], line.start[2])
    
    print "[INFO] LINE.End X: %.2f Y: %.2f Z: %.2f\n" % (line.end[0], line.end[1], line.end[2])

    # Add Xs
    allXCoordinates.append(line.start[0])
    allYCoordinates.append(line.start[1])

    # Add Ys
    allXCoordinates.append(line.end[0])
    allYCoordinates.append(line.end[1])

#
allPolyline = [entity for entity in dwg.entities if entity.dxftype == 'LWPOLYLINE']
for polyline in allPolyline:

    # print "[INFO] Polyline X: %.2f Y: %.2f Z: %.2f\n" % (polyline.points[0], polyline.points[1], polyline.points[2])

    for point in polyline.points:
        allXCoordinates.append(point[0])
        allYCoordinates.append(point[1])

# 
minX = min(allXCoordinates)
maxX = max(allXCoordinates)

minY = min(allYCoordinates)
maxY = max(allYCoordinates)

initCoordinate = [minX, minY]
endCoordinate = [maxX, maxY]

try:
    print "[INFO] X: %.2f Y: %.2f Z: %.2f" % (initCoordinate[0], initCoordinate[1], initCoordinate[2])
except:
    print "[WARNING] Z coordinate not found"



print "[INFO]: Moving to the center of the first hole\n"

lastRadius = 0

allCircles = [entity for entity in dwg.entities if entity.dxftype == 'CIRCLE']
for circle in allCircles:
    if(lastRadius != circle.radius):
        print "[WARNING] Not match radius of %.2f to %.2f\n" % (lastRadius, circle.radius) 

    print "Hole r: %.2f mm\n" % circle.radius

    lastRadius = circle.radius

    distanceX = distanceInX(initCoordinate, circle.center)
    distanceY = distanceInY(initCoordinate, circle.center)
    distanceZ = 0

    # Grbl distances
    dGrblX = distanceX - machinePosition[0]
    dGrblY = distanceY - machinePosition[1]
    dGrblZ = distanceZ - machinePosition[2]

    # Update machine position
    machinePosition[0] = machinePosition[0] + dGrblX
    machinePosition[1] = machinePosition[1] + dGrblY
    machinePosition[2] = machinePosition[2] + dGrblZ


    commands += moveGrblX(dGrblX)
    commands += moveGrblY(dGrblY)

print "[INFO]: Machine position\n"
print "X: %.2f Y: %.2f Z: %.2f\n" % (machinePosition[0], machinePosition[1], machinePosition[2])

print commands
