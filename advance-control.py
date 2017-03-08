#!/usr/bin/env python
"""
advance control with g-code CNC table
"""

# Usage:

# import the necessary packages
import argparse
import serial
import time


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

        print 'Set configuration: ' + line

        # send g-code block to grbl
        serialbus.write(line + '\n')

        # wait for grbl response with carriage return
        grbl_out = serialbus.readline()
        print ' : ' + grbl_out.strip()

    # close file and serial port
    sender_config_file.close()


def send_model_command(serialbus, path_command_file):
    """
    Send command model file (dxf to grbl)

    Args:
        serial (serial): Serial port
        path_command_file (file): Contents of the model (dxf to grbl)
    """

    # open g-code-file
    commands_file = open(path_command_file, 'r')

    #
    # stream g-code to grbl
    for line in commands_file:
        # strip all EOL characters for streaming
        line = line.strip()

        print 'Sending: ' + line

        # send g-code block to grbl
        serialbus.write(line + '\n')

        # wait for grbl response with carriage return
        grbl_out = serialbus.readline()
        print ' : ' + grbl_out.strip()

    # close file and serial port
    commands_file.close()


# construct the argument parse and parse the arguments
a = argparse.ArgumentParser()
a.add_argument("-p", "--serialport", required=True,
    help="Serial Port name")

a.add_argument("-c", "--commandfile", required=True,
    help="Commands file (.nc)")

a.add_argument("-s", "--sender", required=True,
    help="Sender configuration file (.nc)")

a.add_argument("-qh", "--quantityh", required=True,
    help="Number of items (horizontal)")

a.add_argument("-qv", "--quantityv", required=True,
    help="Number of items (vertical)")

args = vars(a.parse_args())


"""
Main Application
"""

quantity_horizontal = args["quantityh"]
quantity_vertical = args["quantityv"]

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

#
send_model_command(s, args["commandfile"])

iterator = 1
while iterator <= quantity_horizontal:
    print iterator
    iterator += 1

# wait here until grbl is finished to cose serial port and file.
raw_input(" Press <Enter> to exit and disable grbl.")

# close serial port
s.close()