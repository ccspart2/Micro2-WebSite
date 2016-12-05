#!/usr/bin/python3

from flask import Flask, render_template
import os, psutil, time, datetime, json
import RPi.GPIO as GPIO
import time
from threading import Timer
import math
from RPIO import PWM
import math
from threading import Thread
import netifaces as ni 


anglePan = 0
angleTilt = 0
servoStepSize = 9

streamingButtonStatus = ""
pictureButtonStatus =""

ShowIp = True
ManualControlEnabled = True

#################################################################
#                                                               #
#               JOYSTICK + BUTTONS                              #
#                                                               #
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

#################################################################
#                                                               #
#               NETWORK DEFINITIONS                             #
#                                                               #
#################################################################

ip = ni.ifaddresses('wlan0')[2][0]['addr']


#################################################################
#                                                               #
#               LCD                                             #
#                                                               #
#################################################################

# Define GPIO to LCD mapping
LCD_RS = 2
LCD_E  = 4
LCD_D4 = 12 
LCD_D5 = 16
LCD_D6 = 8
LCD_D7 = 7


# Define some device constants
LCD_WIDTH = 16    # Maximum characters per line
LCD_CHR = True
LCD_CMD = False

LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line

# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005

# Main program block
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)       # Use BCM GPIO numbers
GPIO.setup(LCD_E, GPIO.OUT)  # E
GPIO.setup(LCD_RS, GPIO.OUT) # RS
GPIO.setup(LCD_D4, GPIO.OUT) # DB4
GPIO.setup(LCD_D5, GPIO.OUT) # DB5
GPIO.setup(LCD_D6, GPIO.OUT) # DB6
GPIO.setup(LCD_D7, GPIO.OUT) # DB7

def lcd_init():
  # Initialise display
  lcd_byte(0x33,LCD_CMD) # 110011 Initialise
  lcd_byte(0x32,LCD_CMD) # 110010 Initialise
  lcd_byte(0x06,LCD_CMD) # 000110 Cursor move direction
  lcd_byte(0x0C,LCD_CMD) # 001100 Display On,Cursor Off, Blink Off
  lcd_byte(0x28,LCD_CMD) # 101000 Data length, number of lines, font size
  lcd_byte(0x01,LCD_CMD) # 000001 Clear display
  time.sleep(E_DELAY)

def lcd_byte(bits, mode):
  # Send byte to data pins
  # bits = data
  # mode = True  for character
  #        False for command

  GPIO.output(LCD_RS, mode) # RS

  # High bits
  GPIO.output(LCD_D4, False)
  GPIO.output(LCD_D5, False)
  GPIO.output(LCD_D6, False)
  GPIO.output(LCD_D7, False)
  if bits&0x10==0x10:
    GPIO.output(LCD_D4, True)
  if bits&0x20==0x20:
    GPIO.output(LCD_D5, True)
  if bits&0x40==0x40:
    GPIO.output(LCD_D6, True)
  if bits&0x80==0x80:
    GPIO.output(LCD_D7, True)

  # Toggle 'Enable' pin
  lcd_toggle_enable()

  # Low bits
  GPIO.output(LCD_D4, False)
  GPIO.output(LCD_D5, False)
  GPIO.output(LCD_D6, False)
  GPIO.output(LCD_D7, False)
  if bits&0x01==0x01:
    GPIO.output(LCD_D4, True)
  if bits&0x02==0x02:
    GPIO.output(LCD_D5, True)
  if bits&0x04==0x04:
    GPIO.output(LCD_D6, True)
  if bits&0x08==0x08:
    GPIO.output(LCD_D7, True)

  # Toggle 'Enable' pin
  lcd_toggle_enable()

def lcd_toggle_enable():
  # Toggle enable
  time.sleep(E_DELAY)
  GPIO.output(LCD_E, True)
  time.sleep(E_PULSE)
  GPIO.output(LCD_E, False)
  time.sleep(E_DELAY)

def lcd_string(message,line):
  # Send string to display

  message = message.ljust(LCD_WIDTH," ")

  lcd_byte(line, LCD_CMD)

  for i in range(LCD_WIDTH):
    lcd_byte(ord(message[i]),LCD_CHR)

# Initialise display
lcd_init()



#################################################################
#                                                               #
#               FLASK APPLICATION                               #
#                                                               #
#################################################################

app = Flask(__name__)


def start_stop_stream(channel):
	if ManualControlEnabled:
		getCommand("toggleStreamButton")
	
def take_pic(channel):
	if ManualControlEnabled:
		getCommand("takePictureButton")

def move_cam(channel):
	global anglePan
	global angleTilt
	moved = False
	
	if not ManualControlEnabled:
			return

	# print("MOVED JOYSTICK IN PIN " + str(channel))
	if GPIO.input(13) == GPIO.LOW and anglePan <= (90-servoStepSize):
		anglePan = anglePan + servoStepSize
		getCommand("move_cam pan " + str(anglePan))
		moved = True
	if GPIO.input(19) == GPIO.LOW and anglePan >= (-90+servoStepSize):
		anglePan = anglePan - servoStepSize
		getCommand("move_cam pan " + str(anglePan))
		moved = True
	if GPIO.input(5) == GPIO.LOW and angleTilt <= (90-servoStepSize):
		angleTilt = angleTilt + servoStepSize
		getCommand("move_cam tilt " + str(angleTilt))
		moved = True
	if GPIO.input(6) == GPIO.LOW and angleTilt >= (-90+servoStepSize):
		angleTilt = angleTilt - servoStepSize
		getCommand("move_cam tilt " + str(angleTilt))
		moved = True

	if moved:
		timer = Timer(0.1, move_cam_manual)
		timer.start()

	#getCommand("positionButton " + str(anglePan) + " " + str(angleTilt))
	# if GPIO.input(channel) == GPIO.HIGH:
	# 	move_cam(channel)


def move_cam_manual():
	global anglePan
	global angleTilt
	moved = False
	
	if not ManualControlEnabled:
			return

	# print("MOVED JOYSTICK IN PIN " + str(channel))
	if GPIO.input(13) == GPIO.LOW and anglePan <= (90-servoStepSize):
		anglePan = anglePan + servoStepSize
		getCommand("move_cam pan " + str(anglePan))
		moved = True
	if GPIO.input(19) == GPIO.LOW and anglePan >= (-90+servoStepSize):
		anglePan = anglePan - servoStepSize
		getCommand("move_cam pan " + str(anglePan))
		moved = True
	if GPIO.input(5) == GPIO.LOW and angleTilt <= (90-servoStepSize):
		angleTilt = angleTilt + servoStepSize
		getCommand("move_cam tilt " + str(angleTilt))
		moved = True
	if GPIO.input(6) == GPIO.LOW and angleTilt >= (-90+servoStepSize):
		angleTilt = angleTilt - servoStepSize
		getCommand("move_cam tilt " + str(angleTilt))
		moved = True

	if moved:
		timer = Timer(0.1, move_cam_manual)
		timer.start()

	#getCommand("positionButton " + str(anglePan) + " " + str(angleTilt))
	# if GPIO.input(channel) == GPIO.HIGH:
	# 	move_cam(channel)


def PictureTakenTimerCB():
	print("Entered timer cb")
	for proc in psutil.process_iter():
		if proc.name() == "raspivid" or proc.name() == "vlc":
			lcd_string("Status:", LCD_LINE_1)
			lcd_string("Streaming", LCD_LINE_2)
			return
	
	lcd_string("Status:", LCD_LINE_1)
	lcd_string("IDLE", LCD_LINE_2) 
	return

def CheckNetworkTimerCB():
	global ip
	global ManualControlEnabled
	response = os.system("ping -c 1 " + ip)
	if response != 0:
		print("network is down!")
		ManualControlEnabled = True
		lcd_string("Network", LCD_LINE_1)
		lcd_string("Disconnected", LCD_LINE_2)
		timer1 = Timer(5, PictureTakenTimerCB)
		timer1.start()

	timer = Timer(5, CheckNetworkTimerCB)
	timer.start()

	return



GPIO.add_event_detect(20, GPIO.FALLING, callback=take_pic, bouncetime=1000)
GPIO.add_event_detect(21, GPIO.FALLING, callback=start_stop_stream, bouncetime=1000)

GPIO.add_event_detect(5, GPIO.FALLING, callback=move_cam, bouncetime=400)
GPIO.add_event_detect(6, GPIO.FALLING, callback=move_cam, bouncetime=400)
GPIO.add_event_detect(13, GPIO.FALLING, callback=move_cam, bouncetime=400)
GPIO.add_event_detect(19, GPIO.FALLING, callback=move_cam, bouncetime=400)


@app.route('/')
def index():

	return render_template('index.html')
	
@app.route('/videos.html')
def videos():
	
	return render_template('videos.html')



@app.route("/<command>")
def getCommand(command):

	global ShowIp
	global ManualControlEnabled
	currentStream = False

	if ShowIp:
		ShowIp = False
		lcd_string("Status:", LCD_LINE_1)
		lcd_string("IDLE", LCD_LINE_2)   
		return "Stopped showing IP on LCD"
	
	print(command)

	words = command.split(' ',2)
	
	for proc in psutil.process_iter():
		if proc.name() == "raspivid" or proc.name() == "vlc":
			currentStream = True
			
			
	if command == "toggleStreamButton":
		if currentStream == True:
			command = "stopStream"
		else:
			command = "startStream"
				
	if command == "startStream":
		if not currentStream:
			print("starting stream ...")
			streamingButtonStatus = "Stream button on stream"
			ts = time.time()
			vidname = str(datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d%H%M%S'))
			command = 'su - pi -c "raspivid -o - -n -t 9999999  -w 800 -h 600 | tee /home/pi/Desktop/Production/Micro2-WebSite/static/videos/' + vidname + '.h264 | cvlc -vvv stream:///dev/stdin --sout \'#standard{access=http,mux=ts,dst=:8080}\' :demux=h264 &"'
			os.system(command)
			lcd_string("Status:", LCD_LINE_1)
			lcd_string("Streaming", LCD_LINE_2)   

	elif words[0] == 'move_cam':
		print(words[2])
		angle = int(words[2])
		angle = int(((angle + 90)/180)*100)
		print(words[1] + " " + words[2])
		if words[1] == "pan":
			os.system("./ServoBlaster/PiBits/ServoBlaster/user/servod --min=67 --max=230 >/dev/null 2>&1") #>/dev/null 2>&1
			os.system("echo 3="+str(angle)+"% > /dev/servoblaster")
		elif words[1] == "tilt":
			os.system("./ServoBlaster/PiBits/ServoBlaster/user/servod --min=60 --max=210 >/dev/null 2>&1")
			os.system("echo 1="+str(angle)+"% > /dev/servoblaster")

	elif command == "stopStream":
		print("stoping stream....")
		streamingButtonStatus = "Stream button off stream"
		os.system('sudo pkill -9 vlc ')
		os.system('sudo pkill -9 raspivid ')
		lcd_string("Status:", LCD_LINE_1)
		lcd_string("IDLE", LCD_LINE_2)   

		
	elif command == "takePictureButton":
		print("Taking picture...")
		lcd_string("Taking new", LCD_LINE_1)
		lcd_string("picture...", LCD_LINE_2)   

		pictureButtonStatus ="Camera Button on"
		os.system('sudo pkill -9 vlc ')
		os.system('sudo pkill -9 raspivid ')	
		ts = time.time()
		picname = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d%H%M%S')
		os.system('raspistill  -n -h 470 -w 470 -o ./static/media/' + str(picname) + '.jpg')
		if currentStream:
			#os.system('su - pi -c "./newStream.sh >/dev/null 2>&1 &"')
			command = 'su - pi -c "raspivid -o - -n -t 9999999  -w 800 -h 600 | tee /home/pi/Desktop/Production/Micro2-WebSite/static/videos/' + picname + '.h264 | cvlc -vvv stream:///dev/stdin --sout \'#standard{access=http,mux=ts,dst=:8080}\' :demux=h264 &"'
			os.system(command)
		
		print("Picture Taken, picture name :" + str(picname))
		lcd_string("New Picture: ", LCD_LINE_1)
		lcd_string(str(picname) + ".jpg", LCD_LINE_2)   

		timer = Timer(5, PictureTakenTimerCB)
		timer.start()
	
	elif words[0] == "manualControl":
		ManualControlEnabled = words[1]  == 'enable'
		print("ManualControlEnabled? " + str(ManualControlEnabled))
		if not ManualControlEnabled:
			lcd_string("Manual Controls", LCD_LINE_1)
			lcd_string("Disabled", LCD_LINE_2)  
		else:
			lcd_string("Status:", LCD_LINE_1)
			if currentStream:
				lcd_string("Streaming", LCD_LINE_2)   
			else:
				lcd_string("IDLE", LCD_LINE_2)   
		

	
	return "success!"


@app.route("/get_images")
def sendImages():
	print("Hay que llevar el mensaje (send images)")
	names = os.listdir(os.path.join(app.static_folder,'media'))
	names.sort(reverse=True)
	print (names)
	return json.dumps(names)
	
	
@app.route("/get_videos")
def sendVideos():
	print("Los videos son el mensaje")
	names = os.listdir(os.path.join(app.static_folder,'videos'))
	names.sort(reverse=True)
	print (names)
	return json.dumps(names)
	
	
def rover_controls():
	pass

if __name__ == '__main__':
	try:
		lcd_string("IP: "+ip, LCD_LINE_1)
		lcd_string("Port :5000", LCD_LINE_2)   
		print("Your Ip is: ")
		print(ip+":5000")
		
		os.system("./ServoBlaster/PiBits/ServoBlaster/user/servod --min=67 --max=230 >/dev/null 2>&1") #>/dev/null 2>&1
		os.system("echo 3=50% > /dev/servoblaster")
		time.sleep(2)
		os.system("./ServoBlaster/PiBits/ServoBlaster/user/servod --min=60 --max=210 >/dev/null 2>&1")
		os.system("echo 1=50% > /dev/servoblaster")

		timer = Timer(5, CheckNetworkTimerCB)
		timer.start()

		app.run(debug=True, use_reloader=False, host='0.0.0.0')
		
	except KeyboardInterrupt:
		pass
		
	finally:
		os.system('sudo pkill -9 vlc ')
		os.system('sudo pkill -9 raspivid ')
		GPIO.cleanup()
		print("Bye bye!")
	
# >/dev/null 2>&1
