#Server Setup on rocky8:
sudo dnf update -y
sudo dnf install -y epel-release
sudo dnf upgrade -y
sudo dnf install git
sudo passwd
git clone https://github.com/rjb25/RoleplayCardGame.git
sudo dnf groupinstall "Development Tools" "Development Libraries"
sudo dnf install wget
cd /tmp/
wget https://www.python.org/ftp/python/3.13.0/Python-3.13.0.tgz
tar -xzvf Python-3.13.0.tgz
cd Python-3.13.0/
./configure --enable-optimizations
make -j $(nproc)
sudo make altinstall
sudo ln -s /usr/local/bin/python3.13 /usr/local/bin/python
cd 
cd RoleplayCardGame
python -m venv ./venv
source ./venv/bin/activate
pip install -r requirements.txt
