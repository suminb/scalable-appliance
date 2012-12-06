sudo service apache2 stop
echo "Installing dependencies..."
sudo apt-get install -y git python-pip python-virtualenv python-dev
echo "Cloning repo..."
git clone https://github.com/cwvh/scalable-maker.git
cd scalable-maker/backend/status/
virtualenv status
source status/bin/activate
pip install psutil flask
deactivate
virtualenv status
source status/bin/activate
echo "Starting status server..."
sudo HOST=0.0.0.0 nohup status/bin/python app.py &
echo "Starting pong worker..."
nohup bash pong.sh &
echo "Done."
exit
