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

__DEBUG__ = False

def port_is_usable(port_name):
    """
    Check if port is usable

    Args:
        port_name
    """

    try:
        serial.Serial(port=port_name)
        return True
    except IOError:
        return False

def valid_int(number):
    """
    Valid integer from string

    Args:
        number
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
    distance = math.sqrt(((abs(end[0]) - abs(start[0])) ** 2) + 0)
    return distance

def distance_in_y(start, end):
    """
    Get distance in Y from two points

    Args:
        start   Start point
        end     End point
    """
    distance = math.sqrt(0 + ((abs(end[1]) - abs(start[1])) ** 2))
    return distance

def get_distance(start, end):
    """
    Get distance from two points

    Args:
        start   Start point
        end     End point
    """
    distance = math.sqrt(((end[0] - start[0]) ** 2) + ((end[1] - start[1]) ** 2))
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

    # # Update machine position
    machine_position[0] = machine_position[0] + d_grbl_x
    machine_position[1] = machine_position[1] + d_grbl_y
    machine_position[2] = machine_position[2] + d_grbl_z

    zero_command = "G91 G00 X%.3fY%.3fZ%.3f\n" % (d_grbl_x, d_grbl_y, d_grbl_z)

    send_grblcode(zero_command, channel)

    print "[INFO]: Machine position\n"
    print "X: %.2f Y: %.2f Z: %.2f\n" % (
        machine_position[0], machine_position[1], machine_position[2])


def make_grbl_move(distances):
    """
    Make Grbl command to move cnc

    Args: x, y, z distances
    """

    cmd_grbl = "G91 G00 X%.3fY%.3fZ%.3f\n" % (distances[0], distances[1], distances[2])

    print "[INFO] GRBL: {}".format(cmd_grbl)

    return cmd_grbl

def drilling(holes, tour, machine_position, channel, mode):
    """
    Drilling holes handler

    Args:
        holes List the coordinates
        tour Best tour for drilling
        base_position Coordinates from last position
        machine_position Coordinates from machine
        channel Ouput channel with device
        mode Automatic or manual mode
    """

    raw_input("Press <Enter> to start drilling...")

    for index in tour:
        hole = holes[index]

        print "\n[DEBUG]: Hole data {}".format(hole)

        # get the distance between the last position of the machine and the new hole
        distance_x = distance_in_x(machine_position, hole)
        distance_y = distance_in_y(machine_position, hole)
        distance_z = 0

        # the movement is positive or negative?
        if hole[0] < machine_position[0]:
            distance_x = distance_x * -1

        if hole[1] < machine_position[1]:
            distance_y = distance_y * -1

        if hole[2] < machine_position[2]:
            distance_z = distance_z * -1

        # get GRBL distances
        d_grbl_x = distance_x
        d_grbl_y = distance_y
        d_grbl_z = distance_z

        # if distance_x < 0
        #     distance_in_x = abs()

        # update machine position
        machine_position[0] = machine_position[0] + distance_x
        machine_position[1] = machine_position[1] + distance_y
        machine_position[2] = machine_position[2] + distance_z

        grbl_command = make_grbl_move((d_grbl_x, d_grbl_y, d_grbl_z))

        send_grblcode(grbl_command, channel)

        print "[INFO]: Machine position X: %.3f Y: %.3f Z: %.3f" % (
            machine_position[0], machine_position[1], machine_position[2])

        if mode == 'A':
            time.sleep(10)
        else:
            # wainting for grbl
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
    hole_tour = []
    all_circles = [entity for entity in dxf_content.entities if entity.dxftype == "CIRCLE"]

    for circle in all_circles:
        # Invertir y for real world
        hole_tour.append((float(circle.center[0]),
                          float(circle.center[1] * -1)))

        hole_list.append((float(circle.center[0]),
                          float(circle.center[1] * -1),
                          float(circle.center[2])))

    return (hole_list, hole_tour)

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

        # Add Xs
        all_x_coordinates.append(line.start[0])
        all_y_coordinates.append(line.start[1])

        # Add Ys
        all_x_coordinates.append(line.end[0])
        all_y_coordinates.append(line.end[1])


    # LWPOLYLINE
    all_polyline = [entity for entity in dxf_content.entities if entity.dxftype == 'LWPOLYLINE']
    for polyline in all_polyline:

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

def set_sender_configuration(channel, path_sender_file):
    """
    Send configuration file for CNC,
    this configuration depends on the RPM of each engine.

    Args:
        serialbus (serial): Serial bus
        path_sender_file (string): Path to sender configuration file
    """

    # open sender configuration
    sender_config_file = open(path_sender_file, 'r')

    # set configuration for drilling
    for line in sender_config_file:
        # strip all EOL characters for streaming
        line = line.strip()

        print "[INFO] Config: {}".format(line)

        send_grblcode(line, channel)

    # close file and serial port
    sender_config_file.close()

def send_grblcode(command, channel):
    """
    Send grbl code to CNC

    Args
        command
        channel
    """

    if not __DEBUG__:
        # send g-code block to grbl
        channel.write(command + '\n')

        # wait for grbl response with carriage return
        grbl_out = channel.readline()
        print ' : ' + grbl_out.strip()

def initialize_grbl(channel, path_config_file):
    """
    Initialize GRBL

    Args:
        channel I/O Device or port
    """

    # wake up grbl
    channel.write("\r\n\r\n")

    # waint for grbl to initialize
    time.sleep(2)

    # flush startup text in serial input
    channel.flushInput()

    set_sender_configuration(channel, path_config_file)


def main():
    """
    Main Application
    """

    output_channel = None
    base_position = [0, 0, 0]
    machine_position = [0, 0, 0]
    mode = "M"
    dxf_content = None
    all_holes = []
    holes_tour = []

    if not __DEBUG__:
        args = argparse.ArgumentParser()
        args.add_argument("-p", "--serialport", required=True,
                          help="Serial Port name")

        args.add_argument("-s", "--sender", required=True,
                          help="Sender configuration file (.nc)")

        args.add_argument("-f", "--dxffile", required=True,
                          help="Model for drilling (.dxf)")

        args.add_argument("-m", "--mode", required=True,
                          help="Manual or Automatic mode")

        args = vars(args.parse_args())

    try:
        if not __DEBUG__:
            # open grbl serial port
            output_channel = serial.Serial(args["serialport"], 9600)

            initialize_grbl(output_channel, args['sender'])

    except IOError:
        print "[ERROR]: Not usable serial port"
        sys.exit(1)

    try:
        if not __DEBUG__:
            dxf_content = dxfgrabber.readfile(args['dxffile'])
        else:
            dxf_content = dxfgrabber.readfile("dxf/drill.dxf")

        print "DXF Version: {}".format(dxf_content.dxfversion)

        base_position = get_base_position(dxf_content)

        print "[INFO] Base Model X: %.2f Y: %.2f Z: %.2f\n" % (
            base_position[0], base_position[1], base_position[2])
    except IndexError:
        print "[INFO] Base Model X: %.2f Y: %.2f" % (base_position[0], base_position[1])
        print "[WARNING] Z coordinate not found\n"

    all_holes, holes_tour = get_holes(dxf_content)

    while True:
        best_tour = tsp.main("tour.png", 10000, "reversed_sections", holes_tour)

        print "[INFO]: Machine Position X: %.2f Y: %.2f Z: %.2f\n" % (
            machine_position[0], machine_position[1], machine_position[2])

        machine_position = drilling(all_holes, best_tour, machine_position,
                                    output_channel, mode)

        print "\nOptions\n"
        print "1) Continue from last position"
        print "2) Finalize"
        option = 3

        option = raw_input('\nOption?: ')

        if valid_int(option):
            option = int(option)

            if option == 1:
                print "[INFO]: Return to start drilling"
            elif option >= 2:
                return_zero(machine_position, output_channel)
                break
        else:
            return_zero(machine_position, output_channel)
            break

    # wait here until grbl is finished to cose serial port and file.
    raw_input(" Press <Enter> to exit and disable grbl.")

    if not __DEBUG__:
        #close serial port
        output_channel.close()

if __name__ == "__main__":
    main()
