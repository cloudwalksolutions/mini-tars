import unittest
from unittest.mock import MagicMock, Mock, patch, call
import asyncio

from gpiozero import LED, Robot, DistanceSensor, Servo

from rover.sensors.distance import UltrasonicDistanceSensor
from rover.sensors.temperature import TemperatureSensor
from rover.sensors.gps import GPSTracker, Location
from rover.sensors.audio import AudioSensor
from rover.sensors.vision import VisionSensor
from rover.arm.arm import RobotArm
from .driver import Driver


class TestDriver(unittest.IsolatedAsyncioTestCase):

    @patch('rover.driver.driver.Driver.stop_if_obstructed')
    @patch('rover.driver.driver.Driver.start_oled_display')
    async def asyncSetUp(self, start_oled_display, stop_if_obstructed):
        self.on_light = MagicMock(spec=LED)

        self.forward_light = MagicMock(spec=LED)
        self.backward_light = MagicMock(spec=LED)
        self.robot1 = MagicMock(spec=Robot)
        self.robot2 = MagicMock(spec=Robot)

        self.detection_light = MagicMock(spec=LED)
        self.distance_threshold = .50
        self.distance_sensor = MagicMock(spec=UltrasonicDistanceSensor)
        self.distance_sensor.distance_display.return_value = f'0.5m'
        self.distance_sensor.object_found.return_value = False
        self.distance_sensor.check_distance.return_value = self.distance_threshold

        self.temperature_sensor = MagicMock(spec=TemperatureSensor)
        self.temperature_sensor.temp_c = Mock(return_value=20.5)
        self.temperature_sensor.temp_f = Mock(return_value=68.9)
        self.temperature_sensor.temp_f_display = Mock(return_value="68.90°")
        self.temperature_sensor.humidity = Mock(return_value=43.9)
        self.temperature_sensor.humidity_display = Mock(return_value="43.90%")

        self.vision_sensor = MagicMock(spec=VisionSensor)
        self.vision_sensor.classify_image.return_value = [('running_shoe', 0.9), ('slipper', 0.1)]

        self.camera_mount_servo = MagicMock(spec=Servo)

        self.gps_tracker = MagicMock(spec=GPSTracker)
        self.gps_tracker.location = Mock(return_value=Location(48.11, 11.51))

        self.audio_sensor = MagicMock(spec=AudioSensor)

        self.robot_arm = MagicMock(spec=RobotArm)

        self.vision_sensor = MagicMock(spec=VisionSensor)
        self.vision_sensor.analyze.return_value = 'running_shoe'

        self.oled_device = MagicMock()

        self.driver = Driver(
            on_light=self.on_light,
            forward_light=self.forward_light,
            backward_light=self.backward_light,
            front_robot=self.robot1,
            back_robot=self.robot2,
            distance_sensor=self.distance_sensor,
            distance_threshold=self.distance_threshold,
            detection_light=self.detection_light,
            temperature_sensor=self.temperature_sensor,
            gps_tracker=self.gps_tracker,
            audio_sensor=self.audio_sensor,
            vision_sensor=self.vision_sensor,
            camera_mount_servo=self.camera_mount_servo,
            arm=self.robot_arm,
            oled_device=self.oled_device,
        )
        self.stop_event = asyncio.Event()

        await self.driver.start(stop_event=self.stop_event)

        self.assertEqual(self.driver.stop_event, self.stop_event)
        self.on_light.on.assert_called_once()
        stop_if_obstructed.assert_called_once_with(self.stop_event)
        start_oled_display.assert_called_once_with(self.stop_event)
        self.assertEqual(self.driver.on_light, self.on_light)
        self.assertEqual(self.driver.detection_light, self.detection_light)
        self.assertEqual(self.driver.forward_light, self.forward_light)
        self.assertEqual(self.driver.backward_light, self.backward_light)
        self.assertEqual(self.driver.front_robot, self.robot1)
        self.assertEqual(self.driver.back_robot, self.robot2)
        self.assertEqual(self.driver.distance_sensor, self.distance_sensor)
        self.assertEqual(self.driver.distance_threshold, self.distance_threshold)
        self.assertEqual(self.driver.temperature_sensor, self.temperature_sensor)
        self.assertEqual(self.driver.gps_tracker, self.gps_tracker)
        self.assertEqual(self.driver.audio_sensor, self.audio_sensor)
        self.assertEqual(self.driver.vision_sensor, self.vision_sensor)
        self.assertEqual(self.driver.camera_mount_servo, self.camera_mount_servo)
        self.assertEqual(self.driver.arm, self.robot_arm)
        self.assertEqual(self.driver.oled_device, self.oled_device)


    def tearDown(self):
        self.driver.shutdown()
        self.on_light.off.assert_called_once()
        self.assertEqual(self.stop_event.is_set(), True)


    def test_invalid_command(self):
        res = self.driver.handle_command("invalid")
        self.assertEqual(res, "invalid command")


    def test_forward(self):
        res = self.driver.handle_command("move:forward")

        self.assertEqual(res, "ack")
        self.robot1.forward.assert_called_once()
        self.robot2.forward.assert_called_once()
        self.forward_light.on.assert_called_once()
        self.backward_light.off.assert_called_once()


    def test_backward(self):
        res = self.driver.handle_command("move:backward")

        self.assertEqual(res, "ack")
        self.robot1.backward.assert_called_once()
        self.robot2.backward.assert_called_once()
        self.backward_light.on.assert_called_once()
        self.forward_light.off.assert_called_once()


    def test_right(self):
        res = self.driver.handle_command("move:right")

        self.assertEqual(res, "ack")
        self.robot1.right.assert_called_once()
        self.robot2.left.assert_called_once()
        self.forward_light.on.assert_called_once()
        self.backward_light.off.assert_called_once()


    def test_left(self):
        res = self.driver.handle_command("move:left")

        self.assertEqual(res, "ack")
        self.robot1.left.assert_called_once()
        self.robot2.right.assert_called_once()
        self.forward_light.on.assert_called_once()
        self.backward_light.off.assert_called_once()


    def test_stop(self):
        res = self.driver.handle_command("move:stop")

        self.assertEqual(res, "ack")
        self.robot1.stop.assert_called_once()
        self.robot2.stop.assert_called_once()
        self.forward_light.off.assert_called_once()
        self.backward_light.off.assert_called_once()

    @patch('rover.driver.driver.Driver.move_camera_mount')
    def test_move_camera_mount_command(self, move_camera_mount):
        res = self.driver.handle_command("camera:left")
        self.assertEqual(res, "ack")
        move_camera_mount.assert_called_once_with("left")

        move_camera_mount.reset_mock()

        res = self.driver.handle_command("camera:right")
        self.assertEqual(res, "ack")
        move_camera_mount.assert_called_once_with("right")


    def test_camera_mount_servo(self):
        self.driver.move_camera_mount("right")
        self.assertEqual(self.driver.camera_mount_position, -1)
        self.camera_mount_servo.min.assert_called_once()

        self.driver.move_camera_mount("right")
        self.assertEqual(self.driver.camera_mount_position, -1)
        self.camera_mount_servo.min.assert_called_once()

        self.driver.move_camera_mount("left")
        self.assertEqual(self.driver.camera_mount_position, 0)
        self.camera_mount_servo.mid.assert_called_once()

        self.driver.move_camera_mount("left")
        self.assertEqual(self.driver.camera_mount_position, 1)
        self.camera_mount_servo.max.assert_called_once()

        self.driver.move_camera_mount("right")
        self.assertEqual(self.driver.camera_mount_position, 0)
        self.assertEqual(self.camera_mount_servo.mid.call_count, 2)

        self.driver.move_camera_mount("right")
        self.assertEqual(self.driver.camera_mount_position, -1)
        self.assertEqual(self.camera_mount_servo.min.call_count, 2)


    def test_handle_arm_rotate_command(self):
        self.driver.handle_arm_command('rotate', 'right')
        self.robot_arm.rotate_base.assert_called_once_with('right')


    def test_handle_arm_shoulder_command(self):
        self.driver.handle_arm_command('shoulder', 'up')
        self.robot_arm.move_shoulder.assert_called_once_with('up')


    def test_handle_arm_elbow_command(self):
        self.driver.handle_arm_command('elbow', 'bend')
        self.robot_arm.move_elbow.assert_called_once_with('bend')


    def test_handle_arm_wrist_pitch_command(self):
        self.driver.handle_arm_command('wrist_pitch', 'up')
        self.robot_arm.pitch_wrist.assert_called_once_with('up')


    def test_handle_arm_wrist_roll_command(self):
        self.driver.handle_arm_command('wrist_roll', 'clockwise')
        self.robot_arm.roll_wrist.assert_called_once_with('clockwise')


    def test_handle_arm_gripper_command(self):
        self.driver.handle_arm_command('gripper', 'close')
        self.robot_arm.operate_gripper.assert_called_once_with('close')


    def test_invalid_arm_command(self):
        response = self.driver.handle_arm_command('unknown', 'something')
        self.assertEqual(response, "invalid arm command")


    async def test_minimal_components(self):
        robot1 = MagicMock(spec=Robot)
        driver = Driver(front_robot=robot1)
        await driver.start()

        res = driver.handle_command("move:forward")
        self.assertEqual(res, "ack")
        robot1.forward.assert_called_once()

        res = driver.handle_command("move:backward")
        self.assertEqual(res, "ack")
        robot1.backward.assert_called_once()

        res = driver.handle_command("move:left")
        self.assertEqual(res, "ack")
        robot1.left.assert_called_once()

        res = driver.handle_command("move:right")
        self.assertEqual(res, "ack")
        robot1.right.assert_called_once()

        res = driver.handle_command("move:stop")
        self.assertEqual(res, "ack")
        robot1.stop.assert_called_once()


    @patch('rover.driver.driver.Driver.stop')
    @patch('rover.driver.driver.Driver.object_out_of_range')
    @patch('rover.driver.driver.Driver.object_in_range')
    async def test_stop_if_obstructed(self, object_in_range, object_out_of_range, stop):
        robot1 = MagicMock(spec=Robot)
        distance_sensor = MagicMock(spec=UltrasonicDistanceSensor)
        distance_sensor.object_found = Mock(return_value=True)
        driver = Driver(
            distance_sensor=distance_sensor,
            distance_threshold=self.distance_threshold,
            front_robot=robot1,
        )
        stop_event = asyncio.Event()

        obstruction_task = asyncio.create_task(driver.stop_if_obstructed(stop_event))

        await asyncio.sleep(0.3)
        distance_sensor.object_found.assert_called_with(self.distance_threshold)
        object_in_range.assert_called_once()
        stop.assert_called_once()

        distance_sensor.object_found = Mock(return_value=False)
        await asyncio.sleep(0.3)
        object_out_of_range.assert_called_once()

        stop_event.set()
        await obstruction_task


    @patch('rover.driver.driver.Driver.disable_forward')
    def test_object_in_range(self, disable_forward):
        self.driver.object_in_range()

        self.detection_light.on.assert_called_once()
        disable_forward.assert_called_once()


    @patch('rover.driver.driver.Driver.enable_forward')
    def test_object_out_of_range(self, enable_forward):
        self.driver.object_out_of_range()

        self.detection_light.off.assert_called_once()
        enable_forward.assert_called_once()


    def test_disable_enable_forward(self):
        self.driver.disable_forward()
        self.assertTrue(self.driver.forward_locked)

        self.driver.forward()
        self.robot1.forward.assert_not_called()

        self.driver.enable_forward()
        self.assertFalse(self.driver.forward_locked)


    @patch('rover.driver.driver.canvas')
    def test_write_to_oled_display(self, canvas):
        mock_draw = MagicMock()

        def canvas_side_effect(*args, **kwargs):
            return MagicMock(__enter__=MagicMock(return_value=mock_draw), __exit__=MagicMock())

        canvas.side_effect = canvas_side_effect

        expected_visual = f'Visual: {self.vision_sensor.analyze()}'
        expected_distance = f'Distance: {self.distance_sensor.distance_display()}'
        expected_temp = f'Temp: {self.temperature_sensor.temp_f_display()}'
        expected_humidity = f'Humidity: {self.temperature_sensor.humidity_display()}'
        expected_location = f'Location: {self.gps_tracker.location().latitude}, {self.gps_tracker.location().longitude}'

        self.driver.write_to_oled_display()

        canvas.assert_called_once_with(self.oled_device)
        calls = [
            call((5, 0), "Cloud Rover", fill="white"),
            call((10, 15), expected_visual, fill="white"),
            call((10, 25), expected_distance, fill="white"),
            call((10, 35), expected_temp, fill="white"),
            call((10, 45), expected_humidity, fill="white"),
            call((10, 55), expected_location, fill="white")
        ]
        mock_draw.text.assert_has_calls(calls, any_order=True)


    async def test_start_oled_display(self):
        write_to_oled_display = MagicMock()
        self.driver.write_to_oled_display = write_to_oled_display
        stop_event = asyncio.Event()

        oled_task = asyncio.create_task(self.driver.start_oled_display(stop_event))

        await asyncio.sleep(0.5)
        stop_event.set()
        await oled_task

        write_to_oled_display.assert_called_once()


    async def test_listen_and_respond(self):
        stop_event = asyncio.Event()
        expected_location = self.gps_tracker.location()
        expected_context = {
            "visual": f"{self.vision_sensor.analyze()}",
            "distance": f"{self.distance_sensor.distance_display()}",
            "temperature": f"{self.temperature_sensor.temp_f_display()}",
            "humidity": f"{self.temperature_sensor.humidity_display()}",
            "location": f"{expected_location.latitude}, {expected_location.longitude}",
        }

        listen_task = asyncio.create_task(self.driver.listen_and_respond(stop_event))

        await asyncio.sleep(2)
        stop_event.set()
        await listen_task
        self.audio_sensor.start_listening.assert_called_with(stop_event)
        self.audio_sensor.respond_to_audio.assert_called_with(expected_context)
