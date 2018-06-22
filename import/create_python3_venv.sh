# source create_python3_venv.sh
python3.6 -m venv --without-pip p3venv
source p3venv/bin/activate
curl https://bootstrap.pypa.io/get-pip.py | python
deactivate
source p3venv/bin/activate
