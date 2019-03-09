# anybody-home
This repository contains the anybody-home application designed to run on a Raspberry Pi 2/3 with the 7" touchscreen under Python 2.7.

It should run on a standard Linux desktop.

---
### Obtain repository:
If you're reading this, chances are you already have some access to it.

&nbsp;&nbsp;&nbsp;&nbsp;`cd ~/<project-dir>/`  
&nbsp;&nbsp;&nbsp;&nbsp;`git clone --recursive https://<github-user>@github.com/delaneymorgan/anybody-home.git`

---
### Auto-Start:
A systemd service is provided for use with Raspbian.  Assuming you have installed homer under /home/pi/project/homer, this should run as is.  Modify as required.

&nbsp;&nbsp;&nbsp;&nbsp;`cd /lib/systemd/system/`  
&nbsp;&nbsp;&nbsp;&nbsp;`sudo ln -s ~/project/homer/anybody-home.service anybody-home.service`  

---
### Packages required:
* redis - in-memory database with persistence

---
### Modules required:
* configparser - .ini file parsing module
* json - json parser/output
* pyping - provides network ping service
* redis - redis interface

&nbsp;&nbsp;&nbsp;&nbsp;`sudo pip install configparser`  
&nbsp;&nbsp;&nbsp;&nbsp;`sudo pip install gunicorn`  
&nbsp;&nbsp;&nbsp;&nbsp;`sudo pip install rpi_backlight`  
&nbsp;&nbsp;&nbsp;&nbsp;`sudo pip install pyowm`  
&nbsp;&nbsp;&nbsp;&nbsp;`sudo pip install untangle`  

---
### Usage:
Give your mobile devices fixed IP addresses in your router.

Add these addresses to the config.ini where indicated.

Restart the service.

Using the redis command line:

redis-cli -n <dbno> -h <host> -p <port>         (default port=6379, default host=127.0.0.1)

scan get "home"
scan get "roll_call"
scan get ""
In your browser:

http://127.0.0.1:<port-no>/tracker

You should see something like:

{
    freds_mobile: true,
    petes_mobile: false
}

-v option can be supplied to enable the (rather limited) console logging.

Most useful parameters can be set via the config.ini file.

---
