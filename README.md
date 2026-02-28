# mini-tars

CloudWalk's Rover "Mini Tars" — a Raspberry Pi powered rover inspired by TARS from Interstellar.

## Architecture

Two separate processes communicate over UDP:

| Component | Language | Runs on | Role |
|-----------|----------|---------|------|
| **Rover** | Python | Raspberry Pi | Hardware I/O, UDP server |
| **Controller** | Go | Laptop | Keyboard GUI, sends UDP commands |

Commands flow as plain text in `type:action` format (e.g. `move:forward`, `arm:rotate:right`). Sensor data streams back as JSON. Video streams separately on port `8080`.

- Controller listens on `0.0.0.0:9000`, connects to rover at `<raspi_ip>:8000`

## Hardware

### Components

| Component | Module/Library |
|-----------|---------------|
| Raspberry Pi | Any model with 40-pin GPIO header |
| 4× DC Motors | [gpiozero Motor](https://gpiozero.readthedocs.io/en/stable/api_output.html#motor) |
| HC-SR04 Ultrasonic Sensor | [gpiozero DistanceSensor](https://gpiozero.readthedocs.io/en/stable/api_input.html#distancesensor-hc-sr04) · [Datasheet](https://components101.com/sensors/ultrasonic-sensor-working-pinout-datasheet) |
| DHT22 Temperature/Humidity Sensor | [adafruit-circuitpython-dht](https://github.com/adafruit/Adafruit_CircuitPython_DHT) · [Wiring guide](https://pimylifeup.com/raspberry-pi-humidity-sensor-dht22/) |
| SSD1306 OLED Display | [luma.oled](https://luma-oled.readthedocs.io/) · I2C address `0x3C` |
| Pi Camera (Picamera2) | [picamera2 docs](https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf) |
| Camera Mount Servo | [gpiozero AngularServo](https://gpiozero.readthedocs.io/en/stable/api_output.html#angularservo) |
| 6-DOF Robot Arm (6× servos) | [gpiozero AngularServo](https://gpiozero.readthedocs.io/en/stable/api_output.html#angularservo) · [Kit link — add yours] |
| UART GPS Module (NMEA) | pynmea2 · [GPS wiring guide](https://randomnerdtutorials.com/raspberry-pi-dht11-dht22-python/) |
| 4× LEDs (status, forward, backward, obstacle) | [gpiozero LED](https://gpiozero.readthedocs.io/en/stable/api_output.html#led) |

### GPIO Pin Reference

> Use [pinout.xyz](https://pinout.xyz/) to cross-reference BCM pin numbers to physical header positions.

#### LEDs

| Pin (BCM) | Component |
|-----------|-----------|
| GPIO 17 | Status / on LED (white) |
| GPIO 4 | Obstacle detection LED (blue) |
| GPIO 22 | Backward indicator LED (red) |
| GPIO 27 | Forward indicator LED (green) |

#### Drive Motors (4× DC, via L298N or equivalent H-bridge)

Each motor needs a forward and reverse pin wired to the H-bridge IN pins.

| Pin (BCM) | Motor | Direction |
|-----------|-------|-----------|
| GPIO 20 | Motor 1 (front-left) | Forward |
| GPIO 21 | Motor 1 (front-left) | Reverse |
| GPIO 23 | Motor 2 (front-right) | Forward |
| GPIO 24 | Motor 2 (front-right) | Reverse |
| GPIO 12 | Motor 3 (rear-left) | Forward |
| GPIO 16 | Motor 3 (rear-left) | Reverse |
| GPIO 6 | Motor 4 (rear-right) | Forward |
| GPIO 13 | Motor 4 (rear-right) | Reverse |

Motors 1+2 form the front axle (`Robot` object), Motors 3+4 form the rear axle. Use `--axles 1` for a single-axle setup.

#### HC-SR04 Ultrasonic Distance Sensor

Wire VCC → 5V, GND → GND. Echo pin requires a voltage divider (5V → 3.3V) to protect the Pi.

| Pin (BCM) | HC-SR04 pin |
|-----------|-------------|
| GPIO 19 | Trigger |
| GPIO 26 | Echo |

Reference: [HC-SR04 datasheet (SparkFun)](https://cdn.sparkfun.com/datasheets/Sensors/Proximity/HCSR04.pdf) · [Wiring guide](https://components101.com/sensors/ultrasonic-sensor-working-pinout-datasheet)

#### DHT22 Temperature & Humidity Sensor

Wire VCC → 3.3V, GND → GND. Place a 10kΩ pull-up resistor between VCC and Data.

| Pin (BCM) | DHT22 pin |
|-----------|-----------|
| GPIO 5 | Data |

Reference: [DHT22 wiring on Raspberry Pi](https://pimylifeup.com/raspberry-pi-humidity-sensor-dht22/) · [Adafruit product page](https://www.adafruit.com/product/385)

#### Camera Mount Servo

| Pin (BCM) | Component |
|-----------|-----------|
| GPIO 14 | Camera mount servo signal |

#### 6-DOF Robot Arm Servos

All servos operate 0–180°. Wire servo VCC/GND to an external 5V supply (not the Pi's 5V pin) to avoid brownouts.

| Pin (BCM) | Joint |
|-----------|-------|
| GPIO 10 | Gripper |
| GPIO 9 | Wrist roll |
| GPIO 0 | Wrist pitch |
| GPIO 11 | Elbow |
| GPIO 15 | Shoulder |
| GPIO 18 | Base rotation |

#### SSD1306 OLED Display (I2C)

| Pi header pin | OLED pin |
|---------------|----------|
| GPIO 2 (SDA) | SDA |
| GPIO 3 (SCL) | SCL |
| 3.3V | VCC |
| GND | GND |

I2C address: `0x3C`. Enable I2C with `sudo raspi-config` → Interface Options → I2C.

Reference: [luma.oled docs](https://luma-oled.readthedocs.io/)

#### GPS Module (UART / NMEA)

Communicates via `/dev/serial0` at 9600 baud. Enable UART with `sudo raspi-config` → Interface Options → Serial Port (disable login shell, enable serial hardware).

| Pi header pin | GPS pin |
|---------------|---------|
| GPIO 14 (TXD) | RXD |
| GPIO 15 (RXD) | TXD |
| 3.3V or 5V | VCC |
| GND | GND |

Any UART GPS module outputting standard NMEA sentences (e.g. Neo-6M) will work.

#### Pi Camera

Connect via CSI ribbon cable. Enable with `sudo raspi-config` → Interface Options → Camera.

Reference: [Picamera2 manual](https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf)

## Commands

### Python (Rover)

```bash
make install        # Install Python dependencies
make test           # Run all Python unit tests with coverage
make coverage       # Run tests + show coverage report
make rover          # Run the rover (all sensors enabled)
make stream         # Run the video streaming server
```

Run a single test:
```bash
python3 -m unittest rover.driver.test_driver.TestDriver.test_forward
```

### Go (Controller)

```bash
make controller                          # Run the controller GUI
go test ./controller/... -run TestName   # Run a single Go test
```

### Deployment (Raspberry Pi)

```bash
make setup          # Initial Pi setup
make deploy         # Enable + start systemd rover.service
make start / stop / restart / status / log
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | When using `--ai` flag | Powers vision and audio AI responses |

## Rover CLI Flags

```
--lights            Enable status LEDs
--axles N           Number of drive axles (1 or 2)
--distance          Enable HC-SR04 obstacle detection
--distance-threshold FLOAT  Detection distance in meters (default: 0.3)
--temperature       Enable DHT22 sensor
--gps               Enable GPS tracker
--audio             Enable audio capture
--ai                Enable OpenAI generative AI
--camera            Enable Pi Camera (vision)
--camera-mount      Enable camera mount servo
--arm               Enable 6-DOF robot arm
--oled              Enable SSD1306 OLED display
```

> **Note:** When not running on a Raspberry Pi, all hardware is automatically replaced with `MagicMock` objects so the rover can be developed and tested on any machine.
