#!/usr/bin/env python
"""
simple g-code streaming script for grbl
"""

# Usage: python basic-control.py --serialport /dev/cu.wchusbserial1420 --commandfile basic-cmd.nc

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

args = vars(a.parse_args())

serialPortName = args["serialport"]

# open grbl serial port
s = serial.Serial(serialPortName, 9600)

# open g-code-file
f = open(args["commandfile"], 'r')

# wake up grbl
s.write("\r\n\r\n")

# wait for grbl to initialize
time.sleep(2)

# flush startup text in serial input
s.flushInput()

# stream g-code to grbl
for line in f:
    # strip all EOL characters for streaming
    l = line.strip()

    print 'Sending: ' + l

    # send g-code block to grbl
    s.write(l + '\n')

    # wait for grbl response with carriage return
    grbl_out = s.readline()
    print ' : ' + grbl_out.strip()

    raw_input(" Press <Enter> to continue...")

# wait here until grbl is finished to cose serial port and file.
raw_input(" Press <Enter> to exit and disable grbl.")

#close file and serial port
f.close()
s.close()
