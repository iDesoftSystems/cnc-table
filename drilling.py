#!/usr/bin/env python
"""
Drilling from dxf file
Optimizes using shorter route (TSP)
"""

# usage: python drilling.py -p COM5 -s config/config.nc -f 1a100mv.dxf -m M

# nececesary packages

import argparse
import dxfgrabber
import math
import serial
import subprocess
import sys
import time
from tsp import tsp

def port_is_usable(portName):
    try:
        ser = serial.Serial(port=portName)
        return True
    except:
        return False

def valid_int(number):
    """
    Valid integer from string
    """
    try:
        int(number)
        return True
    except ValueError:
        return False

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

def return_zero(machine_position, channel):
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

    send_grblcode(cmd_x, channel)
    send_grblcode(cmd_y, channel)
    send_grblcode(cmd_z, channel)

    print "[INFO]: Machine position\n"
    print "X: %.2f Y: %.2f Z: %.2f\n" % (
        machine_position[0], machine_position[1], machine_position[2])



def drilling(holes, tour, base_position, machine_position, channel, mode):
    """
    """

    for index in tour:
        hole = holes[index]

        distance_x = distance_in_x(base_position, hole)
        distance_y = distance_in_y(base_position, hole)
        distance_z = 0

        # GRBL distances
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

        send_grblcode(cmd_x, channel)
        send_grblcode(cmd_y, channel)
        send_grblcode(cmd_z, channel)

        print "Hole {} {}\n".format(index, hole)
        print "[INFO]: Machine position X: %.2f Y: %.2f Z: %.2f\n" % (
            machine_position[0], machine_position[1], machine_position[2])

        if mode == 'A':
            time.sleep(9)
        else:
            time.sleep(2)
            raw_input(" Press <Enter> to continue with next hole...")


    return machine_position

def get_holes(dxf_content):
    """
    Get all coordinates from holes

    Args:
        dxf_content Data from dxf file
    """

    hole_list = []
    all_circles = [entity for entity in dxf_content.entities if entity.dxftype == "CIRCLE"]

    for circle in all_circles:
        hole_list.append((float(circle.center[0]), float(circle.center[1])))

    return hole_list

def get_base_position(dxf_content):
    """
    Get base position from model
    base: [min_x, min_y, min_z]
    end: [max_x, max_y, max_z]

    Args:
        dxf_content Data from dxf file
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
    # max_x = max(all_x_coordinates)

    min_y = min(all_y_coordinates)
    # max_y = max(all_y_coordinates)

    init_coordinate = [min_x, min_y, 0]
    # end_coordinate = [max_x, max_y]

    return init_coordinate

def set_sender_configuration(chanel, path_sender_file):
    """
    Send configuration file for CNC,
    this configuration depends on the RPM of each engine.

    Args:
        serialbus (serial): Serial bus
        path_sender_file (string): Path to sender configuration file
    """

    # open sender configuration
    sender_config_file = open(path_sender_file, 'r')

    #
    # set configuration for drilling
    for line in sender_config_file:
        # strip all EOL characters for streaming
        line = line.strip()

        send_grblcode(line, chanel)

    # close file and serial port
    sender_config_file.close()

def send_grblcode(command, chanel):
    """
    Send grbl code to CNC

    Args
        command
        chanel
    """
    print 'Sending GRBL: ' + command

    # send g-code block to grbl
    # chanel.write(command + '\n')

    # wait for grbl response with carriage return
    # grbl_out = chanel.readline()
    # print ' : ' + grbl_out.strip()

def initialize_grbl(chanel, path_config_file):
    """
    Initialize GRBL

    Args:
        chanel I/O Device or port
    """

    # wake up grbl
    chanel.grite("\r\n\r\n")

    # waint for grbl to initialize
    time.sleep(2)

    # flush startup text in serial input
    chanel.flushInput()

    set_sender_configuration(chanel, path_config_file)


def main():
    """
    Main Application
    """

    output_chanel = None
    base_position = [0, 0, 0]
    machine_position = None
    mode = "M"

    args = argparse.ArgumentParser()
    args.add_argument("-p", "--serialport", required=True,
                      help="Serial Port name")

    args.add_argument("-s", "--sender", required=True,
                      help="Sender configuration file (.nc)")

    args.add_argument("-f", "--dxfile", required=True,
                      help="Model for drilling (.dxf)")

    args.add_argument("-m", "--mode", required=True,
                      help="Manual or Automatic mode")

    args = vars(args.parse_args())

    try:
        # open grbl serial port
        output_chanel = serial.Serial(args["serialport"], 9600)

        initialize_grbl(output_chanel, args['sender'])

    except IOError:
        print "Error"

    try:
        dxf_content = dxfgrabber.readfile(args['dxffile'])

        print "DXF Version: {}".format(dxf_content.dxfversion)

        base_position = get_base_position(dxf_content)
        machine_position = base_position

        print "[INFO] Base Model X: %.2f Y: %.2f Z: %.2f\n" % (
            base_position[0], base_position[1], base_position[2])
    except IndexError:
        print "[INFO] Base Model X: %.2f Y: %.2f" % (base_position[0], base_position[1])
        print "[WARNING] Z coordinate not found\n"

    all_holes = []
    all_holes = get_holes(dxf_content)

    best_tour = tsp.main("tour.png", 10000, "reversed_sections", all_holes)

    while True:
        print "[INFO]: Machine Position X: %.2f Y: %.2f Z: %.2f\n" % (
            machine_position[0], machine_position[1], machine_position[2])

        machine_position = drilling(all_holes, best_tour, base_position,
                                    machine_position, output_chanel, mode)

        print "\nOptions\n"
        print "1) Continue from last position"
        print "2) Finalize"
        option = 3

        option = raw_input('\nOption?: ')
        if valid_int(option):
            if option == 1:
                best_tour = tsp.main("tour.png", 10000, "reversed_sections", all_holes)
            elif option >= 2:
                return_zero(machine_position, output_chanel)
                break
        else:
            return_zero(machine_position, output_chanel)
            break

    # wait here until grbl is finished to cose serial port and file.
    raw_input(" Press <Enter> to exit and disable grbl.")

    #close serial port
    output_chanel.close()

if __name__ == "__main__":
    main()
