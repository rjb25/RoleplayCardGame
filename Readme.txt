#Server Setup on rocky8 :
#NAME="Rocky Linux"
#VERSION="8.10 (Green Obsidian)"
#ID="rocky"
#ID_LIKE="rhel centos fedora"
#VERSION_ID="8.10"
#PLATFORM_ID="platform:el8"
#PRETTY_NAME="Rocky Linux 8.10 (Green Obsidian)"
#ANSI_COLOR="0;32"
#LOGO="fedora-logo-icon"
#CPE_NAME="cpe:/o:rocky:rocky:8:GA"
#HOME_URL="https://rockylinux.org/"
#BUG_REPORT_URL="https://bugs.rockylinux.org/"
#SUPPORT_END="2029-05-31"
#ROCKY_SUPPORT_PRODUCT="Rocky-Linux-8"
#ROCKY_SUPPORT_PRODUCT_VERSION="8.10"
#REDHAT_SUPPORT_PRODUCT="Rocky Linux"
#REDHAT_SUPPORT_PRODUCT_VERSION="8.10"

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
sudo dnf install vim -y
sudo dnf install tmux -y
firewall-cmd --permanent --zone=public --add-port=80/tcp
firewall-cmd --permanent --zone=public --add-port=12345/tcp
firewall-cmd --permanent --zone=public --add-service=http
sudo firewall-cmd --reload

#Cron job is located at /etc/cron.daily/restart-server.sh
#You need to connect to http not https. Browsers will add https.
#You need to add the following path to crontab -e
#PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

sudo dnf install nginx
sudo subscription-manager repos --enable codeready-builder-for-rhel-8-x86_64-rpms
sudo dnf install python3 python-devel gcc
sudo dnf --enablerepo=devel install augeas-devel
sudo dnf install epel-release
sudo dnf install https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm
sudo dnf upgrade
sudo dnf install snapd
sudo systemctl enable --now snapd.socket
sudo ln -s /var/lib/snapd/snap /snap
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/local/bin/certbot
sudo systemctl start nginx
