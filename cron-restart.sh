#Are you connection to the https?
#PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin
source ~/RoleplayCardGame/venv/bin/activate; 
pkill -f 'http.server'
cd ~/RoleplayCardGame; nohup python -um http.server 80 > serveroutput.txt &
pkill -f 'card.py'
cd ~/RoleplayCardGame; nohup python -u card.py > output.txt &
