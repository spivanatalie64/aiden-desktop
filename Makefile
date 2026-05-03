.PHONY: all setup build test lint check clean docs dev-backend dev-web dev-tui dev-gtk

all: check test
	@echo "All checks passed."

setup:
	./build.sh setup

build:
	./build.sh build

test:
	./build.sh test

lint:
	./build.sh lint

check:
	./build.sh check

clean:
	./build.sh clean

docs:
	./build.sh docs

dev-backend:
	./build.sh dev-backend

dev-web:
	./build.sh dev-web

dev-tui:
	./build.sh dev-tui

dev-gtk:
	./build.sh dev-gtk

help:
	./build.sh help
