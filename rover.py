import os
from time import sleep
import asyncio
from unittest.mock import MagicMock, Mock

import asyncclick as click
from gpiozero import LED, Motor, Robot, DistanceSensor, AngularServo
import pygame
import speech_recognition as sr
from picamera2 import Picamera2
from picamera2.previews.null_preview import NullPreview
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306

from rover.driver.driver import Driver
from rover.ai.gen import GenAI
from rover.sensors.distance import UltrasonicDistanceSensor
from rover.sensors.temperature import TemperatureSensor
from rover.sensors.gps import GPSTracker, Location
from rover.sensors.audio import AudioSensor
from rover.sensors.vision import VisionSensor
from rover.arm.arm import RobotArm
from rover.servers.pins import *
from rover.servers.system import is_raspberry_pi
from rover.servers.udp import RoverServerUDP
from rover.servers.tcp import RoverServerTCP
from rover.servers.rover import RoverServer


@click.command()
@click.option('--lights', is_flag=True, help='Enable status LEDs')
@click.option('--axles', default=0, type=int, help='Number of axles')
@click.option('--distance', is_flag=True, help='Enable distance sensor')
@click.option('--distance-threshold', default=.3, type=float, help='Obstacle detection threshold')
@click.option('--temperature', is_flag=True, help='Enable temperature sensor')
@click.option('--gps', is_flag=True, help='Enable GPS tracker')
@click.option('--audio', is_flag=True, help='Enable audio')
@click.option('--ai', is_flag=True, help='Enable generative AI')
@click.option('--camera', is_flag=True, help='Enable camera')
@click.option('--camera-mount', is_flag=True, help='Enable camera mount')
@click.option('--arm', is_flag=True, help='Enable robot arm')
@click.option('--oled', is_flag=True, help='Enable OLED display')
async def run(
        lights,
        axles,
        distance,
        distance_threshold,
        temperature,
        gps,
        audio,
        ai,
        camera,
        camera_mount,
        arm,
        oled,
):

    audio_sensor = None
    if audio:
        gen_ai = None
        if ai:
            gen_ai = GenAI(api_key=os.environ.get("OPENAI_API_KEY"))

        audio_sensor = AudioSensor(gen_ai=gen_ai)

    if not is_raspberry_pi():
        on_led = MagicMock(spec=LED)
        forward_light = MagicMock(spec=LED)
        backward_light = MagicMock(spec=LED)

        robot1 = MagicMock(spec=Robot)
        robot2 = MagicMock(spec=Robot)

        temperature_sensor = MagicMock(spec=TemperatureSensor)
        temperature_sensor.temp_c = Mock(return_value=20.5)
        temperature_sensor.temp_f = Mock(return_value=68.9)
        temperature_sensor.humidity = Mock(return_value=43.9)

        distance_sensor = MagicMock(spec=DistanceSensor)

        gps_tracker = MagicMock(spec=GPSTracker)
        gps_tracker.location = Mock(return_value=Location(48.1, 48.3))

        camera_mount_servo = MagicMock(spec=AngularServo)

        robot_arm = MagicMock(spec=RobotArm)

        oled_device = MagicMock(spec=ssd1306)

        vision_sensor = MagicMock(spec=VisionSensor)

        driver = Driver(
            on_light=on_led,
            forward_light=forward_light,
            backward_light=backward_light,
            front_robot=robot1,
            back_robot=robot2,
            distance_sensor=distance_sensor,
            temperature_sensor=temperature_sensor,
            gps_tracker=gps_tracker,
            audio_sensor=audio_sensor,
            camera_mount_servo=camera_mount_servo,
            arm=robot_arm,
            oled_device=oled_device,
            vision_sensor=vision_sensor,
        )

    else:
        white_led = None
        red_led = None
        green_led = None
        if lights:
            white_led = LED(STATUS_ON_LED_PIN)
            red_led = LED(RED_LED_PIN)
            green_led = LED(GREEN_LED_PIN)

        if audio_sensor is not None:
            audio_sensor.light=white_led

        robot1 = None
        if axles > 0:
            print("USING AT LEAST 1 AXLE")
            motor1 = Motor(forward=M1_FORWARD_PIN, backward=M1_REVERSE_PIN)
            motor2 = Motor(forward=M2_FORWARD_PIN, backward=M2_REVERSE_PIN)
            robot1 = Robot(left=motor1, right=motor2)

        robot2 = None
        if axles == 2:
            print("USING 2 AXLES")
            motor3 = Motor(forward=M3_FORWARD_PIN, backward=M3_REVERSE_PIN)
            motor4 = Motor(forward=M4_FORWARD_PIN, backward=M4_REVERSE_PIN)
            robot2 = Robot(left=motor3, right=motor4)

        distance_sensor = None
        if distance:
            print("USING DISTANCE SENSOR. THRESHOLD: ", distance_threshold)
            blue_led = LED(DISTANCE_LED_PIN)
            uds = DistanceSensor(trigger=TRIGGER_PIN, echo=ECHO_PIN, threshold_distance=distance_threshold)
            distance_sensor = UltrasonicDistanceSensor(uds, blue_led)

        temperature_sensor = None
        if temperature:
            import adafruit_dht
            import board
            print("USING TEMPERATURE SENSOR")
            dht_device = adafruit_dht.DHT22(board.D5)
            temperature_sensor = TemperatureSensor(dht_device)

        gps_tracker = None
        if gps:
            print("USING GPS TRACKER")
            serial_port = "/dev/serial0"
            gps_tracker = GPSTracker(serial_port)

        vision_sensor = None
        if camera:
            print("USING VISION SENSOR")
            camera = Picamera2()
            camera.start_preview(NullPreview())
            vision_sensor = VisionSensor(
                light=white_led,
                camera=camera,
            )

        camera_mount_servo = None
        if camera_mount:
            print("USING CAMERA MOUNT SERVO")
            camera_mount_servo = AngularServo(CAMERA_MOUNT_SERVO_PIN)

        robot_arm = None
        if arm:
            print("USING 6DOF ROBOT ARM")
            robot_arm = RobotArm(
                gripper_servo=AngularServo(ARM_SERVO_PIN_1, min_angle=0, max_angle=180),
                wrist_roll_servo=AngularServo(ARM_SERVO_PIN_2, min_angle=0, max_angle=180),
                wrist_pitch_servo=AngularServo(ARM_SERVO_PIN_3, initial_angle=0, min_angle=0, max_angle=180),
                elbow_servo=AngularServo(ARM_SERVO_PIN_4, min_angle=0, max_angle=180),
                shoulder_servo=AngularServo(ARM_SERVO_PIN_5, initial_angle=110, min_angle=0, max_angle=180),
                base_servo=AngularServo(ARM_SERVO_PIN_6, min_angle=0, max_angle=180),
            )

        oled_device = None
        if oled:
            print("USING OLED DISPLAY")
            serial = i2c(port=1, address=0x3C)
            oled_device = ssd1306(serial)

        driver = Driver(
            on_light=white_led,
            forward_light=green_led,
            backward_light=red_led,
            front_robot=robot1,
            back_robot=robot2,
            distance_sensor=distance_sensor,
            distance_threshold=distance_threshold,
            temperature_sensor=temperature_sensor,
            gps_tracker=gps_tracker,
            audio_sensor=audio_sensor,
            vision_sensor=vision_sensor,
            camera_mount_servo=camera_mount_servo,
            arm=robot_arm,
            oled_device=oled_device,
        )

    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    udp_protocol = RoverServerUDP(loop=loop, stop_event=stop_event, driver=driver)
    tcp_server = RoverServerTCP()
    server = RoverServer(driver=driver, udp_protocol=udp_protocol, tcp_server=tcp_server)

    try:
        await server.listen_and_serve(loop, stop_event)
    finally:
        if robot_arm is not None:
            robot_arm.go_to_starting_position()
        await server.shutdown()


if __name__ == "__main__":
    run(_anyio_backend='asyncio')


