# BYASE-GUI

A GUI (Graphical User Interface) tool for BYASE software.

## Installation

BYASE-GUI is built using the [wxPython](https://wxpython.org/) 
framework, in order to successfully compile the package 
`wxPython`, some system libraries should be pre-installed. 
For example, on **Ubuntu 18.04**, these libraries may need 
to be installed:
```shell
sudo apt install libgtk-3-0 libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev freeglut3-dev libwebkitgtk-3.0-dev libjpeg-dev libtiff-dev
```
The package `pathlib2` may also need to be installed:
```shell
pip3 install --user pathlib2
```
Then BYASE-GUI can be installed by:
```shell
pip3 install --user byase-gui
```
This will automatically install `byase`, 
`wxPython` and `psutil`.


## Documentation

The documentation of BYASE can be found 
[here](https://byase-doc.readthedocs.io/en/latest/).
