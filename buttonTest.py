from flask import Flask, render_template
import os, psutil, time, datetime, json
import RPi.GPIO as GPIO
import time
import math
from RPIO import PWM
import math
from threading import Thread
import netifaces as ni 



GPIO.setmode(GPIO.BCM)
GPIO.setup(21, GPIO.IN)

def take_pic(arg):
	print("Hola")
	
GPIO.add_event_detect(21, GPIO.FALLING, callback=take_pic, bouncetime=200)

while True:
	pass
