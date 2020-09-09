sudo apt update
mkdir /home/ubuntu/downloads

# git
ssh-keygen -t rsa -b 4096 -C "knapiontek@gmail.com"
# hint: add *.pub file to github account settings
git clone git@github.com:knapiontek/trend.git

# arangodb
curl -OL https://download.arangodb.com/arangodb37/DEBIAN/Release.key
sudo apt-key add - < Release.key
echo 'deb https://download.arangodb.com/arangodb37/DEBIAN/ /' | sudo tee /etc/apt/sources.list.d/arangodb.list
sudo apt-get install apt-transport-https
sudo apt-get update
sudo apt-get install arangodb3=3.7.2-1
root:rootpassword
sudo service arangodb3 status

# anaconda
wget -P /home/ubuntu/downloads/ https://repo.anaconda.com/archive/Anaconda3-2020.07-Linux-x86_64.sh
md5sum /home/ubuntu/downloads/Anaconda3-2020.07-Linux-x86_64.sh
1046c40a314ab2531e4c099741530ada  /home/ubuntu/downloads/Anaconda3-2020.07-Linux-x86_64.sh
bash Anaconda3-2020.07-Linux-x86_64.sh
conda env create -n trend-py37 -f requirements.yml
conda env update -n trend-py37 -f requirements.yml
conda activate trend-py37

# certbot
sudo apt install certbot
# hint: stop webserver to allow certbot to make a test on :80
sudo certbot certonly --standalone
sudo cat /etc/letsencrypt/live/gecko-code.info/privkey.pem
sudo certbot renew --dry-run
sudo certbot renew

# nginx
sudo apt-get install nginx
sudo unlink /etc/nginx/sites-enabled/default
sudo cp nginx.conf /etc/nginx/sites-available/nginx.conf
sudo link -s /etc/nginx/sites-available/nginx.conf /etc/nginx/sites-enabled/nginx.conf
sudo service nginx configtest
sudo service nginx restart

# finally
sudo apt-get autoremove

# run
# hint: deploy /home/ubuntu/.trend (see src/config_schema.py)
./run.sh
pkill --echo gunicorn
