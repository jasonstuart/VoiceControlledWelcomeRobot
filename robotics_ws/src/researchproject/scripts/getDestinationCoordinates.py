#!/usr/bin/python
import rospy
import numpy as np
import actionlib
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from std_msgs.msg import String
from actionlib_msgs.msg import *
from tf.transformations import quaternion_from_euler
from geometry_msgs.msg import Pose, Point, Quaternion, Twist
from math import radians, pi
import pyttsx

#class definitions
class Coordinate:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Location:
    def __init__(self, line):
        temp = line.split(",")
        self.coord = Coordinate(temp[0], temp[1])
        self.orientationEuler = float(temp[2]) * pi
        
        #convert the stored euler angle to the robot's quaternion orientation.
        self.quaternion = quaternion_from_euler(0, 0, self.orientationEuler, axes='sxyz')
        self.label = temp[3]
        
    #checks if the given key (found from pocketsphinx) is in this object or not
    def containsLabel(self, key):
        if self.label == key:
            return True
            
        else:
            return False

#loads all the points in the text file into the location class for ease of use
def loadPoints():
    file = open("./src/researchProject/scripts/coordinates.txt", "r")  
    fileContents = file.read().splitlines()
    print(fileContents)
    locations = np.empty([len(fileContents)], object)
    for a in np.arange(0, len(fileContents)):
        locations[a] = Location(fileContents[a])
    
    return locations
 
#simple function that speaks the given string using pythons pyaudio module   
def speak(message):
    engine = pyttsx.init()
    engine.setProperty("rate", 100)
    engine.say(message)
    engine.runAndWait()

#main function
def findCoordinates():
    #initialize the SimpleActionClient that communicates with the base and wait for the base to come online      
    client = actionlib.SimpleActionClient("move_base", MoveBaseAction)
    client.wait_for_server()
    
    #load all the points into a list of objects for use later
    locations = loadPoints()
    print("Waiting for keyword...")
    
    #enter an infinite loop until the program is shutdown
    while not rospy.is_shutdown():
        confirm = "no"
        #wait for a keyword from pocketsphinx and if keyword found, wait for confirmation
        while confirm != "yes":
            speak("Can I help you?")
            key = "no"
            while key == "no" or key == "yes":
                key = rospy.wait_for_message("/pocketsphinx_recognizer/output", String)
                key = key.data
            speak("Do you want me to take you to " + key)  
            confirmData = rospy.wait_for_message("/pocketsphinx_recognizer/output", String)
            confirm = confirmData.data
        speak("Sure, I can take you to " + key)
        print("Keyword Received!")
        #Check Audio speech to text for labels
        
        #we have the keyword, so find the object storing the coordinates
        a = 0
        found = False
        while a < locations.size and not found:
            if locations[a].containsLabel(key):
                found = True
            else:
                a+=1
        
        #now that we have the coordinates, convert it into a "Message" (MoveBaseGoal) that the base can understand
        destination = locations[a].coord
        res = locations[a]
        
        #print(destination.x)
        #print(destination.y)
        
        goal = MoveBaseGoal()
        goal.target_pose.header.frame_id = "map"
        goal.target_pose.header.stamp = rospy.Time.now()
        goal.target_pose.pose.position.x = float(destination.x)
        goal.target_pose.pose.position.y = float(destination.y)
        #print(res.quaternion)
        q = Quaternion(res.quaternion[0], res.quaternion[1], res.quaternion[2], res.quaternion[3])
        goal.target_pose.pose.orientation = q
        #print goal
        
        #now send the message to the base for it to navigate to
        #the function won't return until the robot reached its goal coordinate
        client.send_goal(goal)
        client.wait_for_result()
        #print client.get_result()
        speak("Here we are, we have arrived at " + key + "'s office. I am heading back to the main lobby. Bye!")
        
        #Go back to start using the same method as above, but to a new coordinate
        destination = locations[0].coord
        res = locations[0]
        #print(destination.x)
        #print(destination.y)
        
        goal = MoveBaseGoal()
        goal.target_pose.header.frame_id = "map"
        goal.target_pose.header.stamp = rospy.Time.now()
        goal.target_pose.pose.position.x = float(destination.x)
        goal.target_pose.pose.position.y = float(destination.y)
        #print(res.quaternion)
        q = Quaternion(res.quaternion[0], res.quaternion[1], res.quaternion[2], res.quaternion[3])
        goal.target_pose.pose.orientation = q
        #print goal
        client.send_goal(goal)
        client.wait_for_result()

if __name__ == '__main__':
    try:
        #initialize the node and then call the main function
        rospy.init_node("storedLocation")
        findCoordinates()
    except rospy.ROSInterruptException:
        pass