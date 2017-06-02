# Rasp in a Maze (RIAM)
*A project by Rodrigo Crespo & Meriem El Yamri*

This project is the server part of the project Rasp in a Maze, 
a hardware+software project where two or more motorized raspberries work together to get out of a maze.

To make it work with the app, you need to install the APP:
https://github.com/crelya/riam_monitor



## Initial Configuration in Raspberry Pi

```
sudo apt-get install bluetooth blueman bluez python-gobject python-gobject-2
python-bluez libbluetooth-dev python-dev libbluetooth-dev

sudo nano /lib/systemd/system/bluetooth.service
```
Write the following after the `Exec` line:
```
bluetoothd --noplugin=sap -C
```
````
sudo nano /etc/bluetooth/main.conf
````
Write the following at the file start:
```
DisablePlugins = pnat
```

```
sudo sdptool add SP
```
In order to make our RPi bluetooth visible, we have to use the following command:
```
sudo hciconfig hci0 piscan
```

You can add it to `/etc/rc.local` so that you don't have to type it each time.

## Install requirements
```
pip install -r requirements.txt
```

## Run
```
python logic.py <virtual|real> <app|noapp> <robot-id> <slave-count>"
```
