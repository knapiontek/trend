sudo apt update
sudo apt install certbot

mkdir ~/downloads

# git
ssh-keygen -t rsa -b 4096 -C "knapiontek@gmail.com"
# add *.pub file to github
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
wget -P ~/downloads/ https://repo.anaconda.com/archive/Anaconda3-2020.07-Linux-x86_64.sh
md5sum /home/ubuntu/downloads/Anaconda3-2020.07-Linux-x86_64.sh
1046c40a314ab2531e4c099741530ada  /home/ubuntu/downloads/Anaconda3-2020.07-Linux-x86_64.sh
bash Anaconda3-2020.07-Linux-x86_64.sh
conda env create -n trend-py37 -f requirements.yml
conda env update -n trend-py37 -f requirements.yml
conda activate trend-py37

# run on port 80
sudo apt-get install authbind
sudo touch /etc/authbind/byport/80
sudo chmod 500 /etc/authbind/byport/80
sudo chown $USER /etc/authbind/byport/80
# re-login
export PYTHONPATH=/home/ubuntu/trend
authbind gunicorn src.web:server -b :80
