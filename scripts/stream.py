#!/usr/bin/env python
import rospy
import arducam_mipicamera as arducam
import v4l2 #sudo pip install v4l2
import time
import cv2 #sudo apt-get install python-opencv
from sensor_msgs.msg import Image
from cv_bridge.core import CvBridge, CvBridgeError
import sys
#import cv_bridge


def align_down(size, align):
    return (size & ~((align)-1))

def align_up(size, align):
    return align_down(size + align - 1, align)

def set_controls(camera):
    try:
        print("Reset the focus...")
        camera.reset_control(v4l2.V4L2_CID_FOCUS_ABSOLUTE)
    except Exception as e:
        print(e)
        print("The camera may not support this control.")

    try:
        print("Enable Auto Exposure...")
        camera.software_auto_exposure(enable = True)
        print("Enable Auto White Balance...")
        camera.software_auto_white_balance(enable = True)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    try:
        
        camera = arducam.mipi_camera()
        print("Open camera...")
        camera.init_camera()
        print("Setting the resolution...")
        
        
        fmt = camera.set_resolution(640, 400)
        print("Current resolution is {}".format(fmt))

        rospy.init_node("arducam_ros_node")
        pub = rospy.Publisher("arducam/camera/image_raw", Image, queue_size=1)
        
        bridge = CvBridge()
        exposure_val = rospy.get_param('~exposure')
        cam_gain_val = rospy.get_param('~cam_gain')
        fps_val = rospy.get_param('~fps')
        
        cv2.startWindowThread() # open thread for showing image. Worked much smoother!
        
        print("Capture loop!")
        camera.set_control(v4l2.V4L2_CID_EXPOSURE,exposure_val)
        camera.set_control(v4l2.V4L2_CID_GAIN, cam_gain_val)
        #r = rospy.Rate(3) # set rate of 30 Hz
        while not rospy.is_shutdown():
            
            frame = camera.capture(encoding = 'raw')
            height = int(align_up(fmt[1], 16))
            width = int(align_up(fmt[0], 32))
            
            image = frame.as_array.reshape(height, width)
            
            image_msg = bridge.cv2_to_imgmsg(image)
            image_msg.header.stamp = rospy.Time.now()

            pub.publish(image_msg)
            #cv2.imshow("Arducam", image)
            
            #check if update in camera values occured
            new_exposure_val = rospy.get_param('~exposure')
            new_cam_gain_val = rospy.get_param('~cam_gain')
            new_fps_val = rospy.get_param('~fps')
            
            if new_exposure_val != exposure_val:
                camera.set_control(v4l2.V4L2_CID_EXPOSURE,new_exposure_val)
                exposure_val = new_cam_gain_val
            
            if new_cam_gain_val != cam_gain_val:
                camera.set_control(v4l2.V4L2_CID_GAIN, new_cam_gain_val)
                cam_gain_cal = new_cam_gain_val
                
            if new_fps_val != fps_val:
                fps_val = new_fps_val
                
            cv2.waitKey(1000/fps_val)
          #  r.sleep()


        # Release memory
        del frame
        cv2.destroyAllWindwos() # destroy all windows and threads
        print("Close camera...")
        camera.close_camera()
    except Exception as e:
        print(e)
