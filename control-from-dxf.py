#!/usr/bin/env python
"""
Control after read dxf file
"""

# usage: python control-from-dxf.py -p /dev/cu.wchusbserial1420 -s config/config.nc -f 1a100mv.dxf -m M

# import the necesary packages
import sys
import math
import dxfgrabber
import argparse
import serial
import time
# import cv2

def distance_in_x(start, end):
    """
    Get distance in X from two points

    Args:
        start   Start point
        end     End point
    """
    distance = math.sqrt(((end[0] - start[0]) ** 2) + 0)
    return distance

def distance_in_y(start, end):
    """
    Get distance in Y from two points

    Args:
        start   Start point
        end     End point
    """
    distance = math.sqrt(0 + ((end[1] - start[1]) ** 2))

    # invertimos (Y) para mundo real
    distance = distance * -1
    return distance

def move_grbl_x(distance):

    """
    Get string GRBL command for (X)

    Args:
        distance    Distance for (X) command
    """
    if distance != 0:
        # print "G01 X%.2f" % distance
        return "G91 G0 X%.2f\n" % distance

    return ""

def move_grbl_y(distance):

    """
    Get string GRBL command for (Y)

    Args:
        distance        Distance for (Y) command
    """

    if distance != 0:
        # print "G01 Y%.2f" % distance
        return "G91 G0 Y%.2f\n" % distance

    return ""

def get_object_boundaries(dxf_content):
    """

    Args:
        dxf_content     Data from dxf file
    """

    all_x_coordinates = []
    all_y_coordinates = []

    # LINE
    all_lines = [entity for entity in dxf_content.entities if entity.dxftype == 'LINE']
    for line in all_lines:

        # print "[INFO] LINE.Start X: %.2f Y: %.2f Z: %.2f\n"
        # % (line.start[0], line.start[1], line.start[2])

        # print "[INFO] LINE.End X: %.2f Y: %.2f Z: %.2f\n"
        # % (line.end[0], line.end[1], line.end[2])

        # Add Xs
        all_x_coordinates.append(line.start[0])
        all_y_coordinates.append(line.start[1])

        # Add Ys
        all_x_coordinates.append(line.end[0])
        all_y_coordinates.append(line.end[1])


    # LWPOLYLINE
    all_polyline = [entity for entity in dxf_content.entities if entity.dxftype == 'LWPOLYLINE']
    for polyline in all_polyline:

        # print "[INFO] Polyline X: %.2f Y: %.2f Z: %.2f\n"
        #  % (polyline.points[0], polyline.points[1], polyline.points[2])

        for point in polyline.points:
            all_x_coordinates.append(point[0])
            all_y_coordinates.append(point[1])

    # boundaries with min and max coordinates
    min_x = min(all_x_coordinates)
    max_x = max(all_x_coordinates)

    min_y = min(all_y_coordinates)
    max_y = max(all_y_coordinates)

    init_coordinate = [min_x, min_y]
    end_coordinate = [max_x, max_y]

    return init_coordinate

def set_sender_configuration(output, path_senderconfig_file):
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

        send_grblcode(line, output)

    # close file and serial port
    sender_config_file.close()

def send_grblcode(command, output):
    """
    Send grbl code to CNC

    Args
        command
        output
    """
    print 'Sending GRBL: ' + command

    # send g-code block to grbl
    output.write(command + '\n')

    # wait for grbl response with carriage return
    grbl_out = output.readline()
    print ' : ' + grbl_out.strip()

def drilling(dxf_content, model_position, output, mode_machine):
    """

    Args:
        dxf_content
        model_position
        output
        mode_machine
    """

    # x, y, z (mm)
    machine_position = [0, 0, 0]
    last_radius = 0

    all_circles = [entity for entity in dxf_content.entities if entity.dxftype == 'CIRCLE']
    for circle in all_circles:

        print "[INFO] Moving to the center of the first hole\n"

        if last_radius != circle.radius:
            print "[WARNING] Not match radius of %.2f to %.2f\n" % (last_radius, circle.radius)
            raw_input("Press <Enter> to continue...\n")

        print "Hole Radius: %.2f mm\n" % circle.radius

        last_radius = circle.radius

        distance_x = distance_in_x(model_position, circle.center)
        distance_y = distance_in_y(model_position, circle.center)
        distance_z = 0

        # Grbl distances
        d_grbl_x = distance_x - machine_position[0]
        d_grbl_y = distance_y - machine_position[1]
        d_grbl_z = distance_z - machine_position[2]

        # Update machine position
        machine_position[0] = machine_position[0] + d_grbl_x
        machine_position[1] = machine_position[1] + d_grbl_y
        machine_position[2] = machine_position[2] + d_grbl_z

        cmd_x = "G91 G0 X%.2f\n" % d_grbl_x
        cmd_y = "G91 G0 Y%.2f\n" % d_grbl_y
        cmd_z = "G91 G0 Z%.2f\n" % d_grbl_z

        send_grblcode(cmd_x, output)
        send_grblcode(cmd_y, output)
        send_grblcode(cmd_z, output)

        print "[INFO]: Machine position\n"
        print "X: %.2f Y: %.2f Z: %.2f\n" % (
            machine_position[0], machine_position[1], machine_position[2])

        if mode_machine == 'A':
            time.sleep(9)
        else:
            time.sleep(2)
            raw_input(" Press <Enter> to continue with next hole...")

    return machine_position

def return_zero(machine_position, output):

    """

    Args:
        machine_position
        output
    """

    print "[INFO] Return to zero\n"

    d_grbl_x = machine_position[0] * -1
    d_grbl_y = machine_position[1] * -1
    d_grbl_z = machine_position[2] * -1

    # Update machine position
    machine_position[0] = machine_position[0] + d_grbl_x
    machine_position[1] = machine_position[1] + d_grbl_y
    machine_position[2] = machine_position[2] + d_grbl_z

    cmd_x = "G91 G0 X%.2f\n" % d_grbl_x
    cmd_y = "G91 G0 Y%.2f\n" % d_grbl_y
    cmd_z = "G91 G0 Z%.2f\n" % d_grbl_z

    send_grblcode(cmd_x, output)
    send_grblcode(cmd_y, output)
    send_grblcode(cmd_z, output)

    print "[INFO]: Machine position\n"
    print "X: %.2f Y: %.2f Z: %.2f\n" % (
        machine_position[0], machine_position[1], machine_position[2])


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

a.add_argument("-m", "--mode", required=True,
    help="Manual or Automatic Mode")

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
print "DXF version: {}".format(dwg.dxfversion)

model_position = get_object_boundaries(dwg)

try:
    print "[INFO] X: %.2f Y: %.2f Z: %.2f\n" % (
        model_position[0], model_position[1], model_position[2])
except IndexError:
    print "[INFO] X: %.2f Y: %.2f" % (model_position[0], model_position[1])
    print "[WARNING] Z coordinate not found\n"

while True:

    last_machine_position = drilling(dwg, model_position, s, args["mode"])

    return_zero(last_machine_position, s)

    op_continue = int(raw_input("\nContinue?"))

    if op_continue <= 0:
        break

# wait here until grbl is finished to cose serial port and file.
raw_input(" Press <Enter> to exit and disable grbl.")

#close serial port
s.close()