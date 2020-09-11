## note: lightsail firewall ssh, http, https
sudo apt-get update
mkdir ~/downloads

# git
ssh-keygen -t rsa -b 4096 -C "knapiontek@gmail.com"
## note: add *.pub file to github account settings
git clone git@github.com:knapiontek/trend.git
cd ~/trend

# arangodb
sudo cp arangodb-os /etc/init.d/arangodb-os
sudo update-rc.d arangodb-os defaults
sudo ./arangodb-os
curl -OL https://download.arangodb.com/arangodb37/DEBIAN/Release.key
sudo apt-key add - < Release.key
echo 'deb https://download.arangodb.com/arangodb37/DEBIAN/ /' | sudo tee /etc/apt/sources.list.d/arangodb.list
sudo apt-get install apt-transport-https
sudo apt-get update
sudo apt-get install arangodb3=3.7.2-1
## note: root:root
sudo service arangodb3 status
sudo vim /etc/arangodb3/arangod.conf
sudo service arangodb3 restart

# anaconda
wget -P ~/downloads/ https://repo.anaconda.com/archive/Anaconda3-2020.07-Linux-x86_64.sh
md5sum ~/downloads/Anaconda3-2020.07-Linux-x86_64.sh
1046c40a314ab2531e4c099741530ada  ~/downloads/Anaconda3-2020.07-Linux-x86_64.sh
bash ~/downloads/Anaconda3-2020.07-Linux-x86_64.sh
conda env create -n trend-py37 -f requirements.yml
conda env update -n trend-py37 -f requirements.yml
conda activate trend-py37

# run the app
## note: deploy ~/.trend (see src/config_schema.py)
./run.py --reload-exchanges --update-series --log-to-screen
./web.sh
pkill --echo gunicorn

# certbot
sudo apt-get install certbot
## note: stop webserver to allow certbot to make a test on :80
sudo certbot certonly --standalone
sudo cat /etc/letsencrypt/live/gecko-code.info/privkey.pem
sudo certbot renew --dry-run
sudo certbot renew

# nginx
sudo apt-get install nginx
sudo apt install apache2-utils
sudo htpasswd -c /etc/nginx/.htpasswd admin
sudo unlink /etc/nginx/sites-enabled/default
sudo cp nginx.conf /etc/nginx/sites-available/nginx.conf
sudo ln -s /etc/nginx/sites-available/nginx.conf /etc/nginx/sites-enabled/nginx.conf
sudo service nginx configtest
sudo service nginx restart

# finally
sudo apt-get autoremove
