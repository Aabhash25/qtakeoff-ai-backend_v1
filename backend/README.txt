======================= FOR CELERY ====================================
To make sure Redis always runs when you work:
windows subsystem for linux
Open Ubuntu
Start Redis with:
 
sudo apt install redis
sudo service redis-server start
 
if you are using UBUNTU WSL
redis-server --daemonize yes
redis-cli ping
 
Or, you can even create a shell script to start Redis and then use it each time.
 
celery -A config worker -l info
celery -A config worker --loglevel=info --pool=solo
low work loads
 
celery -A config worker --loglevel=info -P threads
multi tasks simulatenously in seperate threads
 
celery -A config worker --loglevel=info -P event
high numbers of concurrent tasks
 
 
celery -A config.celery_app flower  
 
======================= END CELERY ====================================
 
 
======================= FOR TESTING ====================================
 
coverage erase
coverage run --rcfile=.coveragerc manage.py test
coverage report / coverage html
 
======================= END TESTING ====================================
 
 
================== GIT ============================
 
git init
git add README.md
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/gaganhanglimbu/quantity_takeoff_v4.git
git lfs install
git lfs track "*.pt"
git add .gitattributes
git add backend/models/floor_best.pt
git add backend/models/wall.pt
git add backend/models/window_door_best.pt
git push -u origin main
 
======================== END GIT ========================================================



========================= PRODUCTION SETTINGS ======================

$Env:DJANGO_SETTINGS_MODULE="config.settings.local"

========================= END PRODUCTION SETTINGS ======================



========================= INSTALLATION PROCESS ======================
 
1
pipenv shell
pipenv install
 
 
2
python -m venv venv
venv\Scripts\activate
python -m pip freeze > requirements.txt >>>>> create
pip freeze > requirements.txt >>>>>>>> can also update
pip install --upgrade -r requirements.txt >>>>> upgrade
pip install -r requirements.txt >>>>>>>>> install requirementss
 
 
=============================== END INSTALLATION PROCESS ===========================
refactor and clean up the whole file for production-readiness?

 
--extra-index-url https://download.pytorch.org/whl/cu126
torch==2.7.1
torchaudio==2.7.1
# torch==2.7.1+cu126
# torchaudio==2.7.1+cu126
# torchvision==0.22.1+cu126
torchvision==0.22.1
 
 
=========================================== THINGS TO DO ==============================================

sudo systemctl daemon-reload
sudo systemctl reload nginx
sudo systemctl restart nginx
sudo systemctl restart django-backend
sudo systemctl restart celery
sudo systemctl restart redis

journalctl -u celery.service -f
journalctl -u django-backend.service -f

free -h
htop

redis-cli -h 161.35.123.22 INFO replication
 
=========================================== END THINGS TO DO ==============================================