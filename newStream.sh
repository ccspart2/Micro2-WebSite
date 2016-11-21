#!/bin/bash
raspivid -o videoPepe.h264 -t 9999999 -w 800 -h 600 --hflip -n | cvlc -vvv stream:///dev/stdin --sout '#standard{access=http,mux=ts,dst=:8080}' :demux=h264



