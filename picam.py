#!/usr/bin/python

from flask import Flask, render_template
import os, psutil, time, datetime, json
import RPi.GPIO as GPIO
import time
import math
from RPIO import PWM
import math
from threading import Thread

anglePan = 0
angleTilt = 0
servoStepSize = 15

#################################################################
#																#
#               HARDWARE DEFINITIONS							#
#																#
#################################################################

#Stream Button
GPIO.setmode(GPIO.BCM)
GPIO.setup(20, GPIO.IN)

#Photo Button
GPIO.setup(21, GPIO.IN)

#Joystick
GPIO.setup(5, GPIO.IN)
GPIO.setup(6, GPIO.IN)
GPIO.setup(13, GPIO.IN)
GPIO.setup(19, GPIO.IN)




app = Flask(__name__)



def start_stop_stream(channel):
	print("Im in callback func")
	getCommand("toggleButton")

def move_cam(channel):
	global anglePan
	global angleTilt
	
	#print("MOVED JOYSTICK IN PIN " + str(channel))
	if channel is 13 and anglePan <= (90-servoStepSize):
		anglePan = anglePan + servoStepSize
	elif channel is 19 and anglePan >= (-90+servoStepSize):
		anglePan = anglePan - servoStepSize
	elif channel is 5 and angleTilt <= (90-servoStepSize):
		angleTilt = angleTilt + servoStepSize
	elif channel is 6 and angleTilt >= (-90+servoStepSize):
		angleTilt = angleTilt - servoStepSize

	getCommand("positionButton " + str(anglePan) + " " + str(angleTilt))
	# if GPIO.input(channel) == GPIO.HIGH:
	# 	move_cam(channel)


GPIO.add_event_detect(20, GPIO.RISING, callback=start_stop_stream, bouncetime=5000)
GPIO.add_event_detect(21, GPIO.RISING, callback=start_stop_stream, bouncetime=5000)

GPIO.add_event_detect(5, GPIO.RISING, callback=move_cam, bouncetime=100)
GPIO.add_event_detect(6, GPIO.RISING, callback=move_cam, bouncetime=100)
GPIO.add_event_detect(13, GPIO.RISING, callback=move_cam, bouncetime=100)
GPIO.add_event_detect(19, GPIO.RISING, callback=move_cam, bouncetime=100)


@app.route('/')
def index():

	return render_template('index.html')

@app.route("/<command>")
def getCommand(command):
	words = command.split(' ',2)
    
	print(command)
	currentStream = False
	#print("Im in getcommand")
		
	for proc in psutil.process_iter():
		if proc.name() == "raspivid" or proc.name() == "vlc":
			currentStream = True
			
			
	if command == "toggleButton":
		if currentStream == True:
			command = "stopStream"
		else:
			command = "startStream"
		
				
	if command == "startStream":
		if not currentStream:
			#os.system('su - pi -c "./newStream.sh &"')
			ts = time.time()
			vidname = str(datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d%H%M%S'))
			command = 'su - pi -c "raspivid -o - -n -t 9999999  -w 800 -h 600 --hflip | tee /home/pi/Desktop/Production/Micro2-WebSite/static/videos/' + vidname + '.h264 | cvlc -vvv stream:///dev/stdin --sout \'#standard{access=http,mux=ts,dst=:8080}\' :demux=h264 &"'
			os.system(command)
			
	elif words[0] == 'positionButton':
		print(words[1])
		print(words[2])
		anglePan = int(words[1])
		angleTilt = int(words[2])
		pan = ((anglePan + 90)/180)*100
		tilt = ((angleTilt + 90)/180)*100
		os.system("echo 3="+str(pan)+"% > /dev/servoblaster")
		os.system("echo 1="+str(tilt)+"% > /dev/servoblaster")
		
	elif command == "stopStream":
		print("pare")
		os.system('sudo pkill -9 vlc ')
		os.system('sudo pkill -9 raspivid ')
		
	elif command == "screenshotButton":
		print("photo")
		os.system('sudo pkill -9 vlc ')
		os.system('sudo pkill -9 raspivid ')	
		ts = time.time()
		picname = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d%H%M%S')
		print("Picture Taken, picture name :" + str(picname))
		os.system('raspistill  -n -h 480 -w 470 -o ./static/media/' + str(picname) + '.jpg')
		if currentStream :
			os.system('su - pi -c "./newStream.sh >/dev/null 2>&1 &"')
	return "success!"

@app.route("/get_images")
def sendImages():
	print("Hay que llevar el mensaje")
	names = os.listdir(os.path.join(app.static_folder,'media'))
	print (names)
	return json.dumps(names)
	
	
def rover_controls():
	pass

if __name__ == '__main__':
	
	try:
		app.run(debug=True, host='0.0.0.0')
	except KeyboardInterrupt:
		pass
	finally:
		os.system('sudo pkill -9 vlc ')
		os.system('sudo pkill -9 raspivid ')
		GPIO.cleanup()
		print("Bye bye!")
	
# >/dev/null 2>&1
