# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Mini-Tars is a Raspberry Pi-powered rover inspired by TARS from Interstellar. It has two distinct components:

1. **Rover (Python)** — runs on-device (Raspberry Pi), handles all hardware I/O and exposes a UDP server
2. **Controller (Go)** — runs on a laptop, provides a keyboard-driven GUI that sends UDP commands to the rover

## Commands

### Python (Rover)

```bash
make install        # Install Python dependencies
make test           # Run all Python unit tests with coverage
make coverage       # Run tests + show coverage report (default: make all)
make script         # Test hardware directly via hardware.py
make rover          # Run the rover with all sensors enabled
make stream         # Run the video streaming server
```

Run a single Python test file:
```bash
python3 -m unittest rover.driver.test_driver
```

Run a single test class or method:
```bash
python3 -m unittest rover.driver.test_driver.TestDriver.test_forward
```

### Go (Controller)

```bash
make controller     # Run the controller GUI (go run controller.go)
go test ./controller/...   # Run Go tests
```

Run a single Go test:
```bash
go test ./controller/... -run "TestName"
```

### Deployment (Raspberry Pi)

```bash
make setup          # Initial Pi setup via bin/setup.sh
make deploy         # Enable + start systemd rover.service
make start / stop / restart / status / log
```

## Architecture

### Communication Protocol

Commands flow over **UDP** as plain text strings in `type:action` format (e.g., `move:forward`, `arm:rotate:right`, `sensor:start`). Sensor data streams back as JSON.

- Controller listens on `0.0.0.0:9000`, connects to rover at `10.0.0.104:8000`
- Video streams separately on port `8080`

### Python Rover (`rover/`)

- **`rover.py`** — CLI entry point using `asyncclick`. Detects if running on a Raspberry Pi (`rover/servers/system.py`) and mocks hardware with `MagicMock` when not on Pi.
- **`rover/driver/driver.py`** — Central `Driver` class wiring all hardware together. Handles movement commands, obstacle detection (async), OLED display updates, and audio response.
- **`rover/servers/udp.py`** — `RoverServerUDP` (asyncio `DatagramProtocol`). Routes incoming UDP commands to `Driver` methods, and streams sensor JSON back to registered clients.
- **`rover/servers/rover.py`** — `RoverServer` orchestrator: starts the driver, creates the UDP datagram endpoint, runs for 9 hours.
- **`rover/sensors/`** — Individual sensor wrappers: `distance`, `temperature`, `gps`, `audio`, `vision`
- **`rover/arm/arm.py`** — 6-DOF robot arm with 6 servos (base, shoulder, elbow, wrist pitch/roll, gripper)
- **`rover/ai/gen.py`** — OpenAI integration for vision/audio AI responses

### Go Controller (`controller/`)

- **`controller.go`** (root) — Ebiten game loop entry point. Wires keyboard input to `controller.Game.UpdateButtonState()`. Renders button grid and sensor data overlay.
- **`controller/controller.go`** — `Game` struct managing button state machine, UDP writes, and sensor data streaming. Commands are sent only on state transitions (press/release), not every frame.
- **`controller/controller_test.go`** — Ginkgo/Gomega BDD tests using `MockUDPClient`
- **`controller/mock_udp_client.go`** — Test double for `net.Conn`

### Key Design Patterns

- **Hardware abstraction**: `rover.py` detects Pi via `is_raspberry_pi()` and substitutes `MagicMock` for all hardware objects, enabling development and testing on any machine.
- **Optional sensors**: All hardware components are `None` by default; the driver guards every call with `if self.x is not None`.
- **Async architecture**: The rover uses `asyncio` throughout. Background tasks (obstacle detection, OLED updates, sensor streaming) run as `asyncio.create_task()`.
- **Button state machine**: The Go controller only sends UDP commands on transitions, preventing command flooding on key hold.
- **Test frameworks**: Python uses `unittest` + `coverage`; Go uses Ginkgo v2 + Gomega.

## Environment

- Requires `OPENAI_API_KEY` env var when running with `--ai` flag
- Pi-specific hardware: GPIO pins defined in `rover/servers/pins.py`
- Service configs in `config/` (systemd unit files for rover and stream)
