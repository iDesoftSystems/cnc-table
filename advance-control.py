#!/usr/bin/env python
"""\
advance control with g-code CNC table
"""

# Usage:

# import the necessary packages
import argparse
import serial
import time

# construct the argument parse and parse the arguments
a = argparse.ArgumentParser()
a.add_argument("-p", "--serialport", required=True,
    help="Serial Port name")

a.add_argument("-c", "--commandfile", required=True,
    help="Commands file (.nc)")

a.add_argument("-s", "--sender", required=True,
    help="Sender configuration file (.nc)")

args = vars(a.parse_args())

serialPortName = args["serialport"]

# open g-code-file
commandFile = open(args["commandfile"], 'r')

# sender configuration
senderConfigFile = open(args["sender"], 'r')

# open grbl serial port
s = serial.Serial(serialPortName, 9600)

# wake up grbl
s.write("\r\n\r\n")

# wait for grbl to initialize
time.sleep(2)

# flush startup text in serial input
s.flushInput()

#
# set configuration for drilling
for line in senderConfigFile:
    # strip all EOL characters for streaming
    line = line.strip()

    print 'Set configuration: ' + line

    # send g-code block to grbl
    s.write(line + '\n')

    # wait for grbl response with carriage return
    grbl_out = s.readline()
    print ' : ' + grbl_out.strip()

#
# stream g-code to grbl
for line in commandFile:
    # strip all EOL characters for streaming
    line = line.strip()

    print 'Sending: ' + line

    # send g-code block to grbl
    s.write(line + '\n')

    # wait for grbl response with carriage return
    grbl_out = s.readline()
    print ' : ' + grbl_out.strip()

# wait here until grbl is finished to cose serial port and file.
raw_input(" Press <Enter> to exit and disable grbl.")

# close file and serial port
f.close()
s.close()