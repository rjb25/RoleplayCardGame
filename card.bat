START /D "C:\Users\jason\RoleplayCardGame" %SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe -noexit -command "ngrok start --all" 
START /D "C:\Users\jason\RoleplayCardGame" %SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe -noexit -command "py -m http.server 8000" 
START /D "C:\Users\jason\RoleplayCardGame" %SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe -noexit -command "py card.py" 
