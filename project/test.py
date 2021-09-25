from img_proc import switch_controller as ctrler
import serial
import time

values = bytearray([ord('w'), ord('a'), ord( 's'), ord( 'd'), ord( '1'), ord( '2'), ord( '3'), ord( '4'), ord( '#')])
print(values)
sequence = "wasd1234#"
sequence.encode('ascii')
byte_sequence = bytes(sequence, 'ascii')
print(byte_sequence)
# serialPort = serial.Serial(port="COM4", baudrate=19200, timeout=1)
serialPort = serial.Serial("COM4", baudrate=115200)
time.sleep(10)
serialPort.write(byte_sequence)
time.sleep(2)
serialPort.write(values)
time.sleep(2)
serialPort.write(byte_sequence)
time.sleep(2)
serialPort.write(values)
serialPort.close()
print("Adios")
# ctrler.write_str("33adddddddddddddddddddddddddw#")
# ctrler.close
