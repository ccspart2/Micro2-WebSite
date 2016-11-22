import netifaces as ni 
ip = ni.ifaddresses('wlan0') [2][0]['addr']
print (ip)
