# import the necessary packages
import FileVideoStream as fvs
from imutils.video import FPS
import argparse
import cv2

width = 1280
height = 720

parser = argparse.ArgumentParser('Image device selector')
parser.add_argument(type=int, default= 1,
                    help="Image device selector", dest = 'cap')
args = parser.parse_args()

# print("version")
# opencv_version = cv2.__version__
# print(opencv_version)

cap = fvs.FileVideoStream(args.cap, width = width, height = height).start()

fps = FPS().start()
run = True
while(True):
    # channels)
    frame = cap.read()

    # show the frame and update the FPS counter
    cv2.imshow('frame', frame)
    k = cv2.waitKey(1) & 0xFF
    if k == ord('q'):
        break
    fps.update()

# stop the timer and display FPS information
fps.stop()
print("[INFO] elasped time: {:.2f}".format(fps.elapsed()))
print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))
# When everything done, release the capture
cv2.destroyAllWindows()