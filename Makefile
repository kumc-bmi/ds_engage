MYPY=mypy
PYTHON3=python
FLAKE8=flake8

SRCS=ref_code_gen.py ds_status_sync.py

check: doctest lint
	$(MYPY) --strict $(SRCS)

lint: $(SRCS)
	$(FLAKE8) $(SRCS)

doctest:
	$(PYTHON3) -m doctest $(SRCS)

run: lint check doctest ref_code_gen.py
	$(PYTHON3) ref_code_gen.py

integration_test: lint check doctest
	REDCAP_API_TOKEN=$(REDCAP_API_TOKEN) $(PYTHON3) $(SRC) 2 3

debug: lint check
	$(PYTHON3) $(SRC) --debug

.envrc:
	echo 'layout python3' >.envrc

install-dev-tools:
	pip install mypy flake8
