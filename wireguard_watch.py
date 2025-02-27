import smtplib
import time
import subprocess
import socket
import syslog
import os
import netifaces as ni
from email.mime.text import MIMEText

##########################################################################################################################################################
# This script checks to see if the wireguard client is connecting to the server in the cloud.
# Works on Debian systems that use sysctl to start their daemon
# Change the items here to your specific instance.
# If you want to use gmail you need to apply for your own app password.  If you want to use a different email system you'll have to figure that out.
#
sender = "sender@gmail.com" # - this has been tested with a gmail account.  If you want another email system,  you have to figure it out.
recipients = ["recipient@email.com"] # - if you want multiple recipients separate them by comma 
password = 'google application password' # - You can't use your normal gmail password for this app, you need a gmail application password.  go google it.
wg_server = "192.168.254.1" # - Tunnel IP of the watchguard "server", *NOT* the external IP.
hostname = socket.gethostname()
subject = hostname + " WG Connection Status."
down_file = '/root/down_file.txt' # - location of the down file.  I put it in roots drive, cause you need root to run this file.
smtp_server = 'smtp.gmail.com'
smtp_port = 465
wg_sysctl_start_string = "wg-quick@wgvpn.service"
#
#
##########################################################################################################################################################
def check_wireguard_connection(wg_server, count=1, timeout=2):
    try:
        subprocess.check_output(
            ["ping", "-c", str(count), "-W", str(timeout), wg_server],
            stderr=subprocess.STDOUT,
            universal_newlines=True
            )
        return True
    except subprocess.CalledProcessError:
        return False
        
        

def send_email (body, subject=subject, sender=sender, recipients=recipients, password=password):
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    
    with smtplib.SMTP_SSL(smtp_server, smtp_port) as smtp_server:
        smtp_server.login(sender, password)
        smtp_server.sendmail(sender, recipients, msg.as_string())
    print("message sent")
    
def restart_wgclient():
    try:
        print("Restarting WG Client")
        subprocess.check_call(["systemctl", "restart", wg_sysctl_start_string])
    except subprocess.CalledProcessError as e:
        print("Error restarting Wireguard Service:",e)

def reboot_client():
    try:
        print("Rebooting the client system...")
        subprocess.check_call(["reboot"])
    except subprocess.CalledProcessError as e:
        print("Error Rebooting the System")
        
def down_file_check():
    if os.path.exists(down_file):
        return True
    else:
        return False
    
def update_down_file(count, file):
    try:
        with open(file, 'r+') as f:
            f.write(str(count))
    except Exception as e:
        print("error updating file: ", e)
            

def get_current_failures():
    try:
        with open(down_file, 'r') as f:
            counter = f.read().strip()
            return int(counter)
    except Exception as e:
        print("The following error occored:",e)

def create_down_file(count, file):
    try:
        with open(file, 'w') as f:
            f.write(str(count))
    except Exception as e:
        print("Error Creating file")
    
def delete_down_file():
    try:
        if down_file_check():
            os.remove(down_file)
    except Exception as e:
        print("Error: Deleting file.")
        
def get_iface_ip():
    # Get's the interfaces of the system and then returns a dict of the ips associated with them.  
    # The startswith line removes any vmware made interfaces that break the logic.
    iface_ip ={}
    for iface in ni.interfaces():
        if iface.tolower().startswith('v'):
            continue
        iface_ip[iface] = ni.ifaddresses(iface)[ni.AF_INET][0]['addr']
        
    return iface_ip
        
def create_email_body(msg):
    email_body = f"{msg}\n\n"
    email_body += f"Iface\t:\tIP Addr\n"
    interfaces = get_iface_ip()
    for key,value in interfaces.items():
        email_body += f"\n{key}\t:\t{value}"
        
    return email_body    


def main(): 
    # counter for how many times the system tried to bring the tunnel back up.
    down_count = 0
    wg_up = False
    while not wg_up:
        # If wireguard is down check for the down file and update it with a count. 
        if not check_wireguard_connection(wg_server):
            wg_status_msg = f" No connection to WG Server {wg_server}.  Attempting to restart WG Client."
            down_count += 1
            # If the file exists get the number and increment it by 1.  If it doesn't, create it and add 1 to it.
            if down_file_check():
                down_count = get_current_failures()
                if down_count == 60:
                    delete_down_file()
                    reboot_client()
                down_count += 1
                update_down_file(down_count, down_file)
            else:
                create_down_file(down_count, down_file)    
            
            
            body = create_email_body(wg_status_msg)  
            send_email(body, hostname + wg_status_msg)
            
            restart_wgclient()
            time.sleep(5)
            wg_up = False
        else:
            # if the tunnel is up, and the down_file exists then it will delete the file and send the email.
            # This is useful when wireguard was previously down and then came back up.  You want to be notified
            # when it's down and then come back up, not notified every hour that it's still up.
            wg_status_msg = hostname + " WG connection is up."
            if down_file_check():
                delete_down_file()
                send_email(create_email_body(wg_status_msg),wg_status_msg)
            syslog.syslog(syslog.LOG_INFO, "WIREGUARD INFO: " + wg_status_msg)
            syslog.syslog(syslog.LOG_INFO, "WIREGUARD INFO: " + create_email_body(wg_status_msg))
            wg_up = True
        
if __name__ =="__main__":
    main()
