# variables:
VENV_DIR = venv
PYTHON = python3
PIP = $(VENV_DIR)/bin/pip
ACTIVATE = . $(VENV_DIR)/bin/activate
REQUIREMENTS = requirements.txt
HEUDICONV_VERSION = 1.3.0

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

.PHONY: anat
anat:
	docker run --rm -v $(CURDIR)/MFR-sample_raw:/input:ro -v $(CURDIR):/output:rw -v $(CURDIR)/code:/code:ro \
	nipy/heudiconv:$(HEUDICONV_VERSION) -d /input/data-MRI/MFR{subject}/*IMA \
	-s 01 -o /output -f code/heudiconv_heuristic.py -c dcm2niix --bids --overwrite

.PHONY: defacing
defacing:
	sh code/defacing.sh $(CURDIR)