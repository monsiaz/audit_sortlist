# Makefile pour sortlist-analyzer
.PHONY: install run clean test

install:
	pip install -r requirements.txt

run:
	python3 src/main.py --config config/config.yaml

clean:
	rm -f reports/*.xlsx reports/*.txt

test:
	pytest tests/ 