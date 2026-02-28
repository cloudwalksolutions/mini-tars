
VENV := .venv
BIN := $(VENV)/bin/

all: install coverage

coverage: test calc
cov: coverage

init:
	@echo "⚙️  Setting up virtual environment..."
	@python3 -m venv $(VENV)
	@$(BIN)pip3 install --upgrade pip
	@$(MAKE) install

install:
	@echo "⚙️  Installing dependencies..."
	@$(BIN)pip3 install -r requirements.txt

script:
	@echo "🧪 Testing rover hardware..."
	@python3 hardware.py

.PHONY: rover
rover:
	@$(BIN)python3 rover.py --lights --distance --temperature --audio --ai --camera --camera-mount --axles 1 --oled

stream:
	@echo "📷 Running video streaming server..."
	@$(BIN)python3 rover/servers/stream.py

.PHONY: controller
controller:
	@echo "👾 Running controller..."
	@go run controller.go

test:
	@echo "🧪 Running unit tests..."
	@$(BIN)coverage run -m unittest discover

calc:
	@echo "🧪 Calculating coverage..."
	@$(BIN)coverage report

report:
	@echo "📊 Showing coverage report..."
	@$(BIN)coverage html

mutate:
	@echo "👾 Running Mutation Tester..."
	@mut.py --target rover.rover --unit-test rover.rover.test_driver

setup:
	@echo "⚙️ Setting up Raspberry Pi..."
	@./bin/setup.sh

deploy: start
	@echo "🚀 Deploying rover..."
	@sudo systemctl enable rover.service
	@sudo systemctl daemon-reload

start: status
	@echo "🚀 Starting rover..."
	@sudo systemctl start rover.service

status:
	@sudo systemctl status rover.service

log:
	@journalctl -f -u rover.service

stop: status
	@echo "🛑 Stopping rover..."
	@sudo systemctl stop rover.service

reload:
	@echo "🔄 Reloading systemd daemon..."
	@sudo systemctl daemon-reload

restart: status
	@echo "🔄 Restarting rover..."
	@sudo systemctl restart rover.service

