#!/usr/bin/env python
"""
Control after read dxf file
"""

# usage: 

# import the necesary packages
import math
import dxfgrabber
import serial
import time
import cv2

def distanceInX(start, end):
    """

    Args:
        start Start point
        end End point
    """
    d = math.sqrt( ( (end[0] - start[0] ) ** 2) + 0 )
    return d

def distanceInY(start, end):
    """

    Args:
    """
    d = math.sqrt( 0 + ( ( end[1] - start[1] ) ** 2 ) )

    # invertimos y para mundo real
    d = d * -1
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

def get_object_boundaries(dwg):
    """

    Args:
        dwg Data from dxf file
    """

    allXCoordinates = []
    allYCoordinates = []

    # LINE
    allLines = [entity for entity in dwg.entities if entity.dxftype == 'LINE']
    for line in allLines:

        # print "[INFO] LINE.Start X: %.2f Y: %.2f Z: %.2f\n" % (line.start[0], line.start[1], line.start[2])

        # print "[INFO] LINE.End X: %.2f Y: %.2f Z: %.2f\n" % (line.end[0], line.end[1], line.end[2])

        # Add Xs
        allXCoordinates.append(line.start[0])
        allYCoordinates.append(line.start[1])

        # Add Ys
        allXCoordinates.append(line.end[0])
        allYCoordinates.append(line.end[1])


    # LWPOLYLINE
    allPolyline = [entity for entity in dwg.entities if entity.dxftype == 'LWPOLYLINE']
    for polyline in allPolyline:

        # print "[INFO] Polyline X: %.2f Y: %.2f Z: %.2f\n" % (polyline.points[0], polyline.points[1], polyline.points[2])

        for point in polyline.points:
            allXCoordinates.append(point[0])
            allYCoordinates.append(point[1])

    # boundaries with min and max coordinates
    minX = min(allXCoordinates)
    maxX = max(allXCoordinates)

    minY = min(allYCoordinates)
    maxY = max(allYCoordinates)

    initCoordinate = [minX, minY]
    endCoordinate = [maxX, maxY]

    return initCoordinate

def set_sender_configuration(serialbus, path_senderconfig_file):
    """
    Send configuration file for CNC,
    this configuration depends on the RPM of each engine.

    Args:
        serialbus (serial): Serial bus
        path_senderconfig_file (string): Path to sender configuration file
    """

    # open sender configuration
    sender_config_file = open(path_senderconfig_file, 'r')

    #
    # set configuration for drilling
    for line in sender_config_file:
        # strip all EOL characters for streaming
        line = line.strip()

        send_grblcode(line, serialbus)

    # close file and serial port
    sender_config_file.close()

def send_grblcode(command, output):
    """
    Send grbl code to CNC

    Args
        command
        output
    """
    print 'Set configuration: ' + command

    # send g-code block to grbl
    serialbus.write(command + '\n')

    # wait for grbl response with carriage return
    grbl_out = serialbus.readline()
    print ' : ' + grbl_out.strip()


def drilling(dwg, modelPosition, output):
    """

    Args:
        dwg
        modelPosition
        output
    """

    # x, y, z (mm)
    machinePosition = [0, 0, 0]
    modelPosition = [0, 0, 0]
    lastRadius = 0

    allCircles = [entity for entity in dwg.entities if entity.dxftype == 'CIRCLE']
    for circle in allCircles:
        if(lastRadius != circle.radius):
            print "[WARNING] Not match radius of %.2f to %.2f\n" % (lastRadius, circle.radius)
            raw_input("Press <Enter> to continue...\n") 

        print "Hole r: %.2f mm\n" % circle.radius

        lastRadius = circle.radius

        distanceX = distanceInX(modelPosition, circle.center)
        distanceY = distanceInY(modelPosition, circle.center)
        distanceZ = 0

        # Grbl distances
        dGrblX = distanceX - machinePosition[0]
        dGrblY = distanceY - machinePosition[1]
        dGrblZ = distanceZ - machinePosition[2]

        # Update machine position
        machinePosition[0] = machinePosition[0] + dGrblX
        machinePosition[1] = machinePosition[1] + dGrblY
        machinePosition[2] = machinePosition[2] + dGrblZ

        cmdY = "G91 G0 Y%.2f\n" % dGrblY
        cmdX = "G91 G0 X%.2f\n" % dGrblX

        send_grblcode(cmdX, output)
        send_grblcode(cmdY, output)

        print "[INFO]: Machine position\n"
        print "X: %.2f Y: %.2f Z: %.2f\n" % (machinePosition[0], machinePosition[1], machinePosition[2])

        raw_input(" Press <Enter> to continue with next hole...")

    return machinePosition

def return_zero(machinePosition, output):

    print "[INFO] Return to zero\n"

    machinePosition[0] = machinePosition[0] * -1
    machinePosition[1] = machinePosition[1] * -1
    machinePosition[2] = machinePosition[2] * -1

    cmdX = "G91 G0 X%.2f\n" % machinePosition[0]
    cmdY = "G91 G0 Y%.2f\n" % machinePosition[1]
    cmdZ = "G91 G0 Z%.2f\n" % machinePosition[2]

    send_grblcode(cmdX, output)
    send_grblcode(cmdY, output)
    send_grblcode(cmdZ, output)

"""
Main application
"""

# construct the argument parse and parse the arguments
a = argparse.ArgumentParser()
a.add_argument("-p", "--serialport", required=True,
    help="Serial Port name")

a.add_argument("-s", "--sender", required=True,
    help="Sender configuration file (.nc)")

a.add_argument("-f", "--dxffile", required=True,
    help="Main model for drilling (.dxf)")

args = vars(a.parse_args())

# open grbl serial port
s = serial.Serial(args["serialport"], 9600)

# wake up grbl
s.write("\r\n\r\n")

# wait for grbl to initialize
time.sleep(2)

# flush startup text in serial input
s.flushInput()

#
set_sender_configuration(s, args["sender"])

"""
Start workin drilling
"""

dwg = dxfgrabber.readfile(args["dxffile"])
print("DXF version: {}".format(dwg.dxfversion))

modelPosition = get_object_boundaries(dwg)

try:
    print "[INFO] X: %.2f Y: %.2f Z: %.2f" % (modelPosition[0], modelPosition[1], modelPosition[2])
except:
    print "[WARNING] Z coordinate not found"

print "[INFO] Moving to the center of the first hole\n"

machinePosition = drilling(dwg, modelPosition, s)

# wait here until grbl is finished to cose serial port and file.
raw_input(" Press <Enter> to exit and disable grbl.")

return_zero(machinePosition, s)

#close file and serial port
s.close()