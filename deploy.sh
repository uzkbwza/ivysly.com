cd "$(dirname "$0")" 
echo "deploying site"
echo "copying site to server"
pelican -s publishconf.py
sshpass -p "REDACTED" rsync -avp output/* root@168.235.86.185:/var/www/ivysly.com/public_html --delete