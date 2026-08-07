#!/bin/sh

source env/bin/activate
env/bin/pyside6-uic assets/gui.ui -o ui_mainwindow.py
python main.py
