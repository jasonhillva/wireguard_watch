# Wireguard_Watch
Remote box wireguard status checker

## Descprition:
Wireguard watch is a wireguard tunnel status checker.  It is designed to keep an eye on the status of your wireguard tunnels and if they go down it will restart them or reboot the box.

## Why?
I run penetration tests for companies all over the globe.  In order to do internals I ship a small box that has a debian image that connects to my Wireguard server in the cloud when it boots.  Sometimes the tunnel may go down due to some type of disruption.  Before I would have to ask the remote side to bounce the box, but now I can run wireguard_watch and it will take care of it for me.

## How
Wireguard_Watch pings the wireguard server through the tunnel.  If it can't successfully ping it will create a file and add a counter to that file and send you an email letting you know it's down.  Every *n* minutes it will try to connect again.  Once the script tries 60 times, it will reboot the server.  If the wireguard tunnel comes up it will send you and email and let you know it's back up.

The script must be run from root and set in the crontab.

## Requirements
- Gmail account (or use your own email server, but read notes)
  - Gmail App Password
- Python3
- pip install Netifaces
- Tested on Debian 11/12/kali
  
## Installation
Clone repo to desired location.  Suggest root only folder.  Ensure no one other than root can write to this file.
```
 git clone https://github.com/jasonhillva/wireguard_watch
```

Add line to crontab 
```
crontab -e
```

If you want the file to be run every hour.  Otherwise, adjust the timing to your liking.
```
0 * * * * /usr/bin/python3 /root/wireguard_watch.py
```


  


