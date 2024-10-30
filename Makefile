#!/usr/bin/make -f
# -*- mode:makefile -*-


all: clean \
	start
	sleep 1
	$(MAKE) run-publisher

start:
	$(MAKE) run-icestorm
	
	

run-subscriber:
	gnome-terminal -- bash -c \
	"./subscriber.py --Ice.Config=subscriber.config; bash"

run-publisher:
	gnome-terminal -- bash -c \
	"./publisher.py --Ice.Config=publisher.config; bash"

run-icestorm:
	mkdir -p IceStorm/
	icebox --Ice.Config=icebox.config &

clean:
	$(RM) *.out
	$(RM) -r __pycache__ IceStorm
