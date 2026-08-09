@echo off

call env\Scripts\activate.bat
echo compiling assets\gui.ui to ui_mainwindow.py...
pyside6-uic.exe assets\gui.ui -o ui_mainwindow.py

echo Done.