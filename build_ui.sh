#!/bin/sh

source env/bin/activate
echo "compiling assets/gui.ui to ui_mainwindow.py..."
pyside6-uic assets/gui.ui -o ui_mainwindow.py
echo "Done."
