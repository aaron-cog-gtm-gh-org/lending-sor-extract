PYTHON ?= python3

.PHONY: run test ui
run:
	$(PYTHON) pipeline.py

test:
	$(PYTHON) -m pytest -q

ui:
	$(PYTHON) -m ui.server
