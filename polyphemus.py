import cv2
import sys

from gui import render_crosshairs
from pid import Pid, print_graph
from red_blob_detection import RedBlobDetector

# Set to false if you don't want to show any windows
showGUI = True

controller = Pid(kp=0.2, ki=0.05, kd=0.2)

vision_algorithm = RedBlobDetector()

def move_camera(vehicle, pwm):
    if vehicle:
        pwm = max(pwm, 1) # Ensure we never ask for negative or zero pwm values
        print(pwm)
        msg = vehicle.message_factory.rc_channels_override_encode(1, 1, 0, 0, 0, 0, 0, pwm, 0, 0)
        print(msg)
        vehicle.send_mavlink(msg)
        vehicle.flush()

def disable_camera(vehicle):
    if vehicle:
        msg = vehicle.message_factory.rc_channels_override_encode(1, 1, 0, 0, 0, 0, 0, 0, 0, 0)
        vehicle.send_mavlink(msg)
        vehicle.flush()


def process_stream(video_in, logger, vehicle=None, require_arming=False):
    
    while True:
        frame = get_frame(video_in)
        
        process_frame(logger, frame, vehicle)
        #cv2.imshow("vid",frame)
        
        #if vehicle:
         #   if require_arming and not vehicle.armed:
          #      break
        ch = 0xFF & cv2.waitKey(5)
        if ch == 27:
            break        

    disable_camera(vehicle)

    print ("Done with stream")
    if logger:
        logger.close()
    cv2.destroyAllWindows()
    video_in.release()

def get_frame(videoInput):
	gotNewFrame, frame = videoInput.read()
	if not gotNewFrame:
		print ("Reached EOF or webcam disconnected")
		sys.exit(0) 
	return frame

def process_frame(logger, frame, vehicle):
    if logger:
        logger.log(frame,vehicle)
        
    target = vision_algorithm.detect_target(frame)
    #print(type(target))
    
    camera_pid(target, vehicle)
   
    render_crosshairs(frame, target)    
    if showGUI:
        cv2.imshow("frame", frame)

def camera_pid(target, vehicle):
    if target != None:
        _, cy = target
            
        control = controller.compute(cy, 240)
        print(type(control))
        pwm = control+1500
        pwm = int(pwm)
        move_camera(vehicle, pwm)

        print_graph(cy,pwm) 
