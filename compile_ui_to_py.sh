#!/bin/sh
# For compiling ui/gui.ui to ui_mainwindow.py

source env/bin/activate
env/bin/pyside6-uic assets/gui.ui -o ui_mainwindow.py
echo "Done."
