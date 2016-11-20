from flask import Flask, render_template
import os, psutil, time, datetime, json


app = Flask(__name__)


@app.route('/')
def index():

	return render_template('index.html')

@app.route("/<command>")
def getCommand(command):
	
	
	print(command)
	currentStream = False
	
		
	for proc in psutil.process_iter():
		if proc.name() == "raspivid":
			currentStream = True
	if command == "startStream":
		if not currentStream:
			os.system('su - pi -c "./newStream.sh &"')
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
	
	
	


if __name__ == '__main__':
	app.run(debug=True, host='0.0.0.0')
# >/dev/null 2>&1
