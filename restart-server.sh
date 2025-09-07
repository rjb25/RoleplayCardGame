git add -u
git commit -m "standard update"
git push origin main
ssh root@roleplaycardgame.com "pkill -f 'python card.py'"
ssh root@roleplaycardgame.com "cd RoleplayCardGame; git stash"
ssh root@roleplaycardgame.com "cd RoleplayCardGame; git pull origin main;"
ssh root@roleplaycardgame.com "cd RoleplayCardGame; git stash pop"
ssh root@roleplaycardgame.com "cd RoleplayCardGame; source ./venv/bin/activate; nohup python card.py &"
