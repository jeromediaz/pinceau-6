SHELL := /bin/bash
CHDIR_SHELL := $(SHELL)

PYTHON := python

.ONESHELL:
.SHELLFLAGS += -e

#
# Setup
#
install-poetry:
	brew install pipx
	pipx ensurepath
	pipx install poetry


init-venv:
	@echo "> $@"
	${PYTHON} -m venv ./venv

update-venv: init-venv
	@echo "> $@"
	cd src
	@source ../venv/bin/activate
	pip install --upgrade pip
	pip install -r requirements.txt
	#pip uninstall llama-cpp-python -y
	#export SYSTEM_VERSION_COMPAT=1 &&\
	#CMAKE_ARGS="SYSTEM_VERSION_COMPAT=1 -DCMAKE_OSX_ARCHITECTURES=arm64 -DLLAMA_METAL=on" pip install -U llama-cpp-python --no-cache-dir


test:
	@echo "> $@"
	cd src
	poetry run python test.py

api:
	@echo "> $@"
	cd src
	poetry run python main_api.py

api-prod:
	@echo "> $@"
	cd src
	poetry run gunicorn -b "0.0.0.0:8000" -w 1 --threads 100 'main_api:create_app()'

api-nh:
	@echo "> $@"
	cd src
	nohup poetry run python main_api.py &

worker:
	@echo "> $@"
	cd src
	#poetry run celery -A worker worker --pool=solo --loglevel=INFO
	poetry run celery -A worker worker --pool=threads --concurrency=1 --loglevel=INFO

check:
	@echo "> $@"
	poetry run black src/
	poetry run mypy src/

build-front:
	@echo "> $@"
	cd etc/admin/pinceau6
	yarn install
	yarn build

poetry-update:
	@echo "> $@"
	export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring
	poetry install

sonar:
	sonar-scanner -Dsonar.organization=jdiaz-fr -Dsonar.projectKey=pinceau6-python -Dsonar.sources=src -Dsonar.host.url=https://sonarcloud.io
