# variables:
VENV_DIR = venv
PYTHON = python3
PIP = $(VENV_DIR)/bin/pip
ACTIVATE = . $(VENV_DIR)/bin/activate
REQUIREMENTS = requirements.txt

.PHONY: all
all: install

# create virtual environment
.PHONY: venv
venv:
	$(PYTHON) -m venv $(VENV_DIR)

# install dependencies
.PHONY: install
install: venv $(REQUIREMENTS)
	$(PIP) install --upgrade pip
	$(PIP) install -r $(REQUIREMENTS)

# freeze current dependencies to requirements.txt
.PHONY: freeze
freeze: venv
	$(PIP) freeze > $(REQUIREMENTS)