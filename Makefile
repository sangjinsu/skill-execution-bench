PYTHON ?= python3
GO ?= go

GO_BIN := skills/go-binary/bin/skill-runner
GO_SRC := ./skills/go-binary/cmd/skill-runner

TOPO_GO_BIN := skills/toposort-go-binary/bin/toposort-runner
TOPO_GO_SRC := ./skills/toposort-go-binary/cmd/toposort-runner

.PHONY: setup test build-go build-go-toposort bench clean

setup:
	$(PYTHON) -m pip install --quiet pytest || \
		echo "Could not install pytest automatically; install it manually if 'make test' fails."

build-go: build-go-toposort
	$(GO) build -o $(GO_BIN) $(GO_SRC)
	@echo "Built $(GO_BIN)"

build-go-toposort:
	$(GO) build -o $(TOPO_GO_BIN) $(TOPO_GO_SRC)
	@echo "Built $(TOPO_GO_BIN)"

test:
	$(PYTHON) -m pytest

bench: build-go
	$(PYTHON) -m harness.run_benchmark

clean:
	rm -f $(GO_BIN) $(TOPO_GO_BIN)
	rm -f outputs/traces/*.jsonl
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	@echo "Cleaned generated outputs and Go binaries."
