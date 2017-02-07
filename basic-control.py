#!/usr/bin/env python
"""\
simple g-code streaming script for grbl
"""

# import necessary packages
import serial
import time

# open grbl serial port
s = serial.Serial('/dev/cu.wchusbserial1420', 9600)

# open g-code-file
f = open('basic-cmd.nc', 'r')

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

# wait here until grbl is finished to cose serial port and file.
raw_input(" Press <Enter> to exit and disable grbl.")

#close file and serial port
f.close()
s.close()
