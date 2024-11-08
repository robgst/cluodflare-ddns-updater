This script updates a dns record in your Cloudflare account to match 
your current public IP address.\
First it checks your IP address, and if it is different from the IP address in your 
Cloudflare dns record, it updates the dns record in Cloudflare.\
It will run automatically at preset intervals.

### Prerequisites
To run this script you need a Cloudflare User API Token \
with the following Permissions:\
Zone - Zone - Read\
Zone - DNS - Edit\
and the following Zone Resources:\
Include - Specific zone - yourdomain.xxx

These permissions are necessary to check the names and IDs of your dns records (Zone Read)\
and to change the IP address of a particular record (DNS Edit).

During setup, the script checks if crontab is installed and accessible.\
If not, it will exit. In this case you should setup crontab or run the script as root.\
In Debian 12 all users have crontab available\
In Alpine linux the user needs to run crontab -e, and write a comment line to enable crontab.

### How to obtain a Cloudflare API Token
Login to Cloudflare\
Click on My Profile (top right)\
Click on API Tokens\
Click on the 'Create Token' button\
Click on the 'Use template' button of Edit zone DNS\
Modify Permissions so that you have the following settings:\
Zone - Zone - Read  \
Zone - DNS - Edit    \
and the following Zone Resources:\
Include - Specific zone - yourdomain.xxx\
Click on the 'Continue to summary' button\
Click on the 'Create Token' button.\
Save the Token


### Security

The Cloudflare token input is not visible on most terminals (similar to Linux password) and is 
saved in a json file readable only by the user (and root).


### Installation
To install on recent Linux systems use pipx.\
On older systems you can use pip.
  
On Debian or Ubuntu  
- `apt install pipx`

On Alpine Linux  
- `apk add pipx`  

Once installed:  
- `pipx ensurepath`  
- Logout and login again (or reboot)  
- `pipx install cloudflare-ddns-updater`  
  
### Setup
To setup the program  
- `cloudflare-ddns-updater --setup`  
  
To change IP check interval  
- `cloudflare-ddns-updater --cron`  
  
To stop automatic ip update  
- `cloudflare-ddns-updater --stop`  
  
To resume automatic IP update  
- `cloudflare-ddns-updater --start`  

To change log level
- `cloudflare-ddns-updater --logs`  

To remove all files created by the script  
- `cloudflare-ddns-updater --cleanup`  

To check the logs
- follow the log file path shown after installation
  
To uninstall
- `cloudflare-ddns-updater --cleanup`
- `pipx uninstall cloudflare-ddns-updater`




Changes:\
1.0.1 - Added log entries for cron changes\
1.0.0 - First official release

