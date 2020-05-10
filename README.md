# BYASE-GUI

A GUI (Graphical User Interface) tool for BYASE software.

## Installation

To use BYASE-GUI, BYASE should be installed first, the installation 
of BYASE is documented [here](https://github.com/ncjllld/byase).

BYASE-GUI is built using the [wxPython](https://wxpython.org/) 
framework, in order to successfully compile the package 
`wxPython`, some system libraries should be pre-installed. 
For example, on **Ubuntu 18.04**, these libraries may need 
to be installed:
```shell
sudo apt install libgtk-3-0 libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev freeglut3-dev libwebkitgtk-3.0-dev libjpeg-dev libtiff-dev
```
Then, use `pip` to install dependent packages:
```shell
pip3 install --user psutil
pip3 install --user wxPython
```

Then, use `pip` to install BYASE-GUI:
```shell
pip3 install --user byase-gui
```

*After the installation, if you cannot run `byase-gui` from the terminal, 
this is caused by the executable binary file `byase-gui` not being found 
in the system path, you may need to run:*
```shell
export PATH=~/.local/bin:$PATH
``` 


## Documentation

The documentation of BYASE can be found 
[here](https://byase-doc.readthedocs.io/en/latest/).
