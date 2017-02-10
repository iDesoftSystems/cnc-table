#!/usr/bin/env python
"""\
Read dxf file
"""

# usage:

# import the necesary packages
import math
import dxfgrabber

dwg = dxfgrabber.readfile("24KA-60mV-test.dxf")
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

def sendCommandGrbl():
    print "G01 X0Y0Z0"
    print "G01 X"

def moveGrblX(distance):

    if(distance != 0):
        print "G01 X%.2f" % distance

def moveGrblY(distance):

    if(distance != 0):
        print "G01 Y%.2f" % distance

# Global var
allXCoordinates = []
allYCoordinates = []

machinePosition = [0, 0, 0]

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

    print "[INFO] Polyline X: %.2f Y: %.2f Z: %.2f\n" % (polyline.points[0], polyline.points[1], polyline.points[2])

    for point in polyline.points:
        allXCoordinates.append(point[0])
        allYCoordinates.append(point[1])

# 
minX = min(allXCoordinates)
maxX = max(allXCoordinates)

minY = min(allYCoordinates)
maxY = max(allYCoordinates)

# print "Min X: %f" % (minX)
# print "Max X: %f" % (maxX)
# print "Min Y: %f" % (minY)
# print "Max Y: %f" % (maxY)

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


    moveGrblX(dGrblX)
    moveGrblY(dGrblY)


# for e in all_layer_0_entities:
#     # 2.7489
#     if e.dxftype() == 'LINE':
#         print("LINE on layer: %s\n" % e.dxf.layer)
#         # print("start point: %s\n" % e.dxf.start)
#         # print("end point: %s\n" % e.dxf.end)

#     if e.dxftype() == 'CIRCLE':
#         print "CIRCLE on layer: %s\n" % e.dxf.layer

print "[INFO]: Machine position\n"
print "X: %.2f Y: %.2f Z: %.2f\n" % (machinePosition[0], machinePosition[1], machinePosition[2])
