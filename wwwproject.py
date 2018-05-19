import array
import sys
import struct
from gopigo import *
import usb.core
import usb.util
import numpy as np
import RPi.GPIO as GPIO
import time
import operator
import pickle
import collections
from operator import itemgetter
import random
import numpy as np
import Adafruit_PCA9685
import smbus
import math
import threading


servo_num = 8
servo_min = 150  
servo_max = 500  
servo_mid = 400
file = open( "/dev/input/mice", "rb" );
pwm = Adafruit_PCA9685.PCA9685()
pwm.set_pwm_freq(60)
speed=150
debug = 0
angles = []
senses = []
acc=[]
flag=0
set_speed(speed)
max_dis = 0
sum_array=[]
def getMouseEvent():
    buf = file.read(3)
    button = ord( buf[0] )
    bLeft = button & 0x1
    bMiddle = ( button & 0x4 ) > 0
    bRight = ( button & 0x2 ) > 0
    x,y = struct.unpack( "bb", buf[1:] )
    if debug:
        print ("L:%d, M: %d, R: %d, x: %d, y: %d\n" % (bLeft,bMiddle,bRight, x, y) )
    return [bLeft,bMiddle,bRight,x,y]

def scaling(x):
    OldMax = 1
    OldMin = -1
    NewMax = 600

    NewMin = 150
    OldValue = x
    OldRange = (OldMax - OldMin)
    if (OldRange == 0):
        NewValue = NewMin
    else:
        NewRange = (NewMax - NewMin)  
        NewValue = (((OldValue - OldMin) * NewRange) / OldRange) + NewMin
    return (NewValue)

def getMouseData(idd, results):

	a=[0]*3
	print (threading.currentThread().getName(), 'Starting '+str(idd))
	while( not exitFlag[idd] ):
        	[l,m,r,x,y]=getMouseEvent() #Get the inputs from the mouse
#		print("getMouseData")
        # if debug:
        #     print l,m,r,x,y
        # print x,"\t",y
        	if y >20:
            		#print("forward")  
            		a[0] = a[0]+y
        	elif y<-20:
            		#print("Back")  
            		a[0] = a[0]+y
        	elif x<-20:
            		#print("left") 
                    a[1] = a[1]+x
                    a[2] = a[2]+abs(x)
        	elif x>20:
            		#print("right")    
                    a[1] = a[1]+x
                    a[2] = a[2]+x
        	time.sleep(.01)
		results[idd] = a
	print (threading.currentThread().getName(), 'Exiting '+str(idd))

def set_servo_pulse(channel, pulse):
    pulse_length = 1000000    # 1,000,000 us per second
    pulse_length //= 60       # 60 Hz
    print('{0}us per period'.format(pulse_length))
    pulse_length //= 4096     # 12 bits of resolution
    print('{0}us per bit'.format(pulse_length))
    pulse *= 1000
    pulse //= pulse_length
    pwm.set_pwm(channel, 0, pulse)

print('Moving servo on channel 0, press Ctrl-C to quit...')
def servo(action):
    print (action)
    action = list(map(scaling,action))
    for i in range(8):
        pwm.set_pwm(i, 0,int( action[i]))
    sleep(.1)

def servoControl(idd,test_angles,test_angles2):
    print (threading.currentThread().getName(), 'Starting '+str(idd))
    for u in range(servo_num):
    	servo(test_angles)
        servo(test_angles2)
    print (threading.currentThread().getName(), 'Exiting '+str(idd))
    exitFlag[idd] = 1
    
def sleep(x):
    time.sleep(x)

def writeToFile(data, filename):
    with open(filename, 'wb') as fp:
        pickle.dump(data, fp)

def loadFromFile(filename):
    with open (filename , 'rb') as fp:
        a = pickle.load(fp)
    return a
    
def learningLoop(learning_episodes):
    a = []
    i=0
    print("VVV")
    for i in range(learning_episodes):
        print("\n\n"+str(i)+"\n\n")
        test_angles = np.zeros(servo_num)
        test_angles2 = np.zeros(servo_num)
        test_angles = np.random.choice([-.15,.15],servo_num)
   #     test_angles2 = np.random.choice([-.25,0,.25],servo_num)

        for v in range(servo_num):
            test_angles2[v]=np.random.choice([-.15,.15],1)
            while test_angles2[v] == test_angles[v]:
                test_angles2[v]=np.random.choice([-.15,.15],1)

        t = threading.Thread(name='getMouseDataThread', target=getMouseData,args=(i,results))
        w = threading.Thread(name='servoControl', target=servoControl,args=(i,test_angles,test_angles2))

        t.start()
        w.start()
        w.join()
        t.join()
	print(results)
        a.append([results[i][0],results[i][1],results[i][2],[test_angles,test_angles2]])
#	servo([0,0,0,0,0,0,0,0])   
#	servo([0,0,0,0,0,0,0,0])   
#	servo([0,0,0,0,0,0,0,0])   
       	sleep(.2)
	if i % 5==0:
		sleep(2)
    return a

learning_episodes = 100
exitFlag = [0]*learning_episodes
results = [None] * learning_episodes
#while True:
#	servo([0,0,0,0,0,0,0,0])
#        servo([ 0.25,  0.25,0.25 ,0.25 ,  0.25,   0.25,   0.25 ,    0.25  ])
#	servo([ -0.25,   - 0.25,    -0.25 ,- 0.25 ,  -0.25,   -0.25,   -0.25 ,    -0.25  ])
#	servo([ 0.25, -0.25, -0.25 , 0.  , -0.25 , 0.  , -0.25, -0.25])
#a = learningLoop(learning_episodes)

#writeToFile(a,'8servo_Test9')
a = loadFromFile('8servo_Test9')
a_sorted = sorted(a, key=itemgetter(0),reverse=True)
a_sorted_2 = sorted(a, key=itemgetter(1),reverse=True)
print  (a_sorted)
print  (a_sorted_2)

forward = a_sorted[:5]
forward = sorted(forward,key=lambda row: np.abs(row[1]))

print  ("forward")
print  (forward)

Back = a_sorted[-5:]
Back = sorted(Back,key=lambda row: np.abs(row[1]))

print  ("Back")
print  (Back)

left = a_sorted_2[-5:]
left = sorted(left,key=lambda row: np.abs(row[0]))

print  ("left")
print  (left)

right = a_sorted_2[:5]
right = sorted(right,key=lambda row: np.abs(row[0]))

print  ("right")
print  (right)
###############################################
print  ("forward")
#sleep(3)
for pp in range(0):
    print  ("forward")
    for p in range(100):
        print(forward[pp])
        servo(forward[pp][3][0])
        servo(forward[pp][3][1])
    sleep(1)

print  ("Back")
#sleep(3)
for pp in range(0):
    print  ("Back")
    for p in range(40):
        print(Back[pp])
        servo(Back[pp][3][0])
        servo(Back[pp][3][1])
    sleep(1)
print  ("right")
#sleep(3)
for pp in range(0):
    print  ("right")
    for p in range(40):
        print(right[pp])
        servo(right[pp][3][0])
        servo(right[pp][3][1])
    sleep(1)
print  ("left")
#sleep(3)
for pp in range(0):
    print  ("left")
    for p in range(40):
        print(left[pp])
        servo(left[pp][3][0])
        servo(left[pp][3][1])
    sleep(1)
errorCounter = 0

#results = [None] * 10
last_error_i = 0
i=0
while True:
    
    t = threading.Thread(name='getMouseDataThread', target=getMouseData,args=(i,results))
    w = threading.Thread(name='servoControlLoop', target=servoControl,args=(i,forward[0][3][0],forward[0][3][1]))

    t.start()
    w.start()
    w.join()
    t.join()    
    
    i=i+1
    if i > 9:
        print(results)
        a = np.array(results[1:10])
	print(a)
        avgFB = a.mean(axis=0)
	
	print("HIIII \n\n\n")
	print(forward[0][0])
	
        print(avgFB[0]) 
	print(avgFB[1])
	print(abs(avgFB[1])) 
        if ((avgFB[0]+400) < forward[0][0]) or (abs(avgFB[1])-50 > forward[0][1]):
	    print(avgFB[0]+100)
	    print("learing again")
            a = learningLoop(100)
	    writeToFile(a,'8servo_Test9_again')
            a_sorted = sorted(a, key=itemgetter(0),reverse=True)
            print  (a_sorted)
            forward = a_sorted[:5]
            forward = sorted(forward,key=lambda row: np.abs(row[1]))
            print  (forward)

        i=0