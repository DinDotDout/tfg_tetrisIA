import cv2
import argparse
import serial
import select
import struct
import sys
import time
import math
import pygame
import numpy

parser = argparse.ArgumentParser('Tetris gameing')
parser.add_argument(type=int, default= 1,
                    help="Image device selector", dest = 'cap')
args = parser.parse_args()

opencv_version = cv2.__version__
(major, minor, patch) = cv2.__version__.split(".")
opencv_version_major = int(major, base=10)
opencv_version_minor = int(minor, base=10)
opencv_version_patch = int(patch, base=10)

print(opencv_version_major)
print(opencv_version_minor)
print(opencv_version_patch)

cap = cv2.VideoCapture(args.cap, cv2.CAP_DSHOW)

def testDevice(cap):
    if cap is None or not cap.isOpened():
       print('Warning: unable to open video source')

testDevice(cap) # no printout

cap.set(3, 1280)
cap.set(4, 720)

# cap.set(3, 1920)
# cap.set(4, 1080)

print(cap.get(0))
print(cap.get(1))
print(cap.get(2))
print(cap.get(3))
print(cap.get(4))
print(cap.get(5))
print(cap.get(6))

width = cap.get(3)
height = cap.get(4)
aspect = (float)(width)/(float)(height)
print("Dimension:" + str(width) + "x" + str(height))
print("Aspect:" + str(aspect))

run = True
while(run):
    _, frame = cap.read()


    # Our operations on the frame come here
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Display the resulting frame
    # width = int(frame.shape[1])
    # height = int(frame.shape[0])
    # dim = (int(width), int(height))
    # resized = cv2.resize(frame, dim, interpolation=cv2.INTER_LINEAR)
    cv2.imshow('frame', frame)
    k = cv2.waitKey(1) & 0xFF
    if k == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()