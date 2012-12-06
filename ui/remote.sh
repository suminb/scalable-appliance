sudo service apache2 stop
sudo apt-get install -y git python-pip python-virtualenv python-dev
git clone https://github.com/cwvh/scalable-maker.git
cd scalable-maker/backend/status/
virtualenv status
source status/bin/activate
pip install psutil flask
deactivate
virtualenv status
source status/bin/activate
sudo HOST=0.0.0.0 nohup status/bin/python app.py &
