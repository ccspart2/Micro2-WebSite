#!/usr/bin/python

from flask import Flask, render_template
import os, psutil, time, datetime, json
import RPi.GPIO as GPIO
import time
import math
from RPIO import PWM
import math
from threading import Thread
import netifaces as ni 


anglePan = 0
angleTilt = 0
servoStepSize = 15

streamingButtonStatus = ""
pictureButtonStatus =""

#################################################################
#																#
#               JOYSTICK + BUTTONS								#
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

#################################################################
#																#
#               NETWORK DEFINITIONS								#
#																#
#################################################################

ip = ni.ifaddresses('wlan0')[2][0]['addr']


#################################################################
#																#
#               LCD												#
#																#
#################################################################

# Define GPIO to LCD mapping
LCD_RS = 2
LCD_E  = 4
LCD_D4 = 24 
LCD_D5 = 25
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


    
#lcd_string("   INIT   ", LCD_LINE_1)
#lcd_string(ip, LCD_LINE_2)    


#################################################################
#																#
#               FLASK APPLICATION								#
#																#
#################################################################

app = Flask(__name__)



def start_stop_stream(channel):
	
	getCommand("toggleButton")
	print(streamingButtonStatus)
	
def take_pic(channel):
	getCommand("screenshotButton")
	print(pictureButtonStatus)

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


GPIO.add_event_detect(20, GPIO.RISING, callback=take_pic, bouncetime=5000)
GPIO.add_event_detect(21, GPIO.RISING, callback=start_stop_stream, bouncetime=5000)

GPIO.add_event_detect(5, GPIO.RISING, callback=move_cam, bouncetime=100)
GPIO.add_event_detect(6, GPIO.RISING, callback=move_cam, bouncetime=100)
GPIO.add_event_detect(13, GPIO.RISING, callback=move_cam, bouncetime=100)
GPIO.add_event_detect(19, GPIO.RISING, callback=move_cam, bouncetime=100)

os.system("sudo ./ServoBlaster/PiBits/ServoBlaster/user/servod")


@app.route('/')
def index():

	return render_template('index.html')
	
@app.route('/videos.html')
def videos():
	
	return render_template('videos.html')
	
	

	
	


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
			print("starting stream ...")
			streamingButtonStatus = "Stream button on stream"
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
		print("stoping stream....")
		streamingButtonStatus = "Stream button off stream"
		os.system('sudo pkill -9 vlc ')
		os.system('sudo pkill -9 raspivid ')
		
	elif command == "screenshotButton":
		print("Taking picture...")
		pictureButtonStatus ="Camera Button on"
		os.system('sudo pkill -9 vlc ')
		os.system('sudo pkill -9 raspivid ')	
		ts = time.time()
		picname = datetime.datetime.fromtimestamp(ts).strftime('%Y%m%d%H%M%S')
		print("Picture Taken, picture name :" + str(picname))
		os.system('raspistill  -n -h 470 -w 470 -o ./static/media/' + str(picname) + '.jpg')
		if currentStream :
			os.system('su - pi -c "./newStream.sh >/dev/null 2>&1 &"')
	return "success!"

@app.route("/get_images")
def sendImages():
	print("Hay que llevar el mensaje")
	names = os.listdir(os.path.join(app.static_folder,'media'))
	print (names)
	return json.dumps(names)
	
	
@app.route("/get_videos")
def sendVideos():
	print("Los videos son el mensaje")
	names = os.listdir(os.path.join(app.static_folder,'videos'))
	print (names)
	return json.dumps(names)
	
	
	
def rover_controls():
	pass

if __name__ == '__main__':
	
	try:
		print("Your IP to enter in browser is: ")
		print(ip+":5000")
		app.run(debug=True, host='0.0.0.0')
	except KeyboardInterrupt:
		pass
	finally:
		os.system('sudo pkill -9 vlc ')
		os.system('sudo pkill -9 raspivid ')
		GPIO.cleanup()
		print("Bye bye!")
	
# >/dev/null 2>&1
