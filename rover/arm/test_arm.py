import unittest
from unittest.mock import MagicMock
from gpiozero import AngularServo

from .arm import RobotArm


class TestRobotArm(unittest.TestCase):
    def setUp(self):
        self.base_servo = MagicMock(spec=AngularServo, angle=None)
        self.shoulder_servo = MagicMock(spec=AngularServo, angle=None)
        self.elbow_servo = MagicMock(spec=AngularServo, angle=None)
        self.wrist_pitch_servo = MagicMock(spec=AngularServo, angle=None)
        self.wrist_roll_servo = MagicMock(spec=AngularServo, angle=None)
        self.gripper_servo = MagicMock(spec=AngularServo, angle=None)

        self.arm = RobotArm(
            gripper_servo=self.gripper_servo,
            wrist_roll_servo=self.wrist_roll_servo,
            wrist_pitch_servo=self.wrist_pitch_servo,
            elbow_servo=self.elbow_servo,
            shoulder_servo=self.shoulder_servo,
            base_servo=self.base_servo,
        )

    def test_starting_position(self):
        self.arm.go_to_starting_position()

        self.assertEqual(self.gripper_servo.angle, 0)
        self.assertEqual(self.wrist_roll_servo.angle, 0)
        self.assertEqual(self.wrist_pitch_servo.angle, 0)
        self.assertEqual(self.elbow_servo.angle, 0)
        self.assertEqual(self.shoulder_servo.angle, 110)
        self.assertEqual(self.base_servo.angle, 0)


    def test_rotate_base_right_increases_angle(self):
        self.base_servo.angle = 90
        self.arm.rotate_base('right')
        self.assertEqual(self.base_servo.angle, 95)


    def test_rotate_base_left_decreases_angle(self):
        self.base_servo.angle = 90
        self.arm.rotate_base('left')
        self.assertEqual(self.base_servo.angle, 85)


    def test_move_shoulder_up_increases_angle(self):
        self.shoulder_servo.angle = 70
        self.arm.move_shoulder('up')
        self.assertEqual(self.shoulder_servo.angle, 75)


    def test_move_shoulder_down_decreases_angle(self):
        self.shoulder_servo.angle = 70
        self.arm.move_shoulder('down')
        self.assertEqual(self.shoulder_servo.angle, 65)


    def test_move_elbow_bend_increases_angle(self):
        self.elbow_servo.angle = 100
        self.arm.move_elbow('bend')
        self.assertEqual(self.elbow_servo.angle, 105)


    def test_move_elbow_extend_decreases_angle(self):
        self.elbow_servo.angle = 100
        self.arm.move_elbow('extend')
        self.assertEqual(self.elbow_servo.angle, 95)


    def test_pitch_wrist_up_increases_angle(self):
        self.wrist_pitch_servo.angle = 45
        self.arm.pitch_wrist('up')
        self.assertEqual(self.wrist_pitch_servo.angle, 50)


    def test_pitch_wrist_down_decreases_angle(self):
        self.wrist_pitch_servo.angle = 45
        self.arm.pitch_wrist('down')
        self.assertEqual(self.wrist_pitch_servo.angle, 40)


    def test_roll_wrist_clockwise_increases_angle(self):
        self.wrist_roll_servo.angle = 30
        self.arm.roll_wrist('clockwise')
        self.assertEqual(self.wrist_roll_servo.angle, 35)


    def test_roll_wrist_counterclockwise_decreases_angle(self):
        self.wrist_roll_servo.angle = 30
        self.arm.roll_wrist('counterclockwise')
        self.assertEqual(self.wrist_roll_servo.angle, 25)


    def test_operate_gripper_open_sets_angle(self):
        self.arm.operate_gripper('open')
        self.assertEqual(self.gripper_servo.angle, 180)


    def test_operate_gripper_close_sets_angle(self):
        self.arm.operate_gripper('close')
        self.assertEqual(self.gripper_servo.angle, 0)


    def test_servo_angle_limits(self):
        """Test that servo angles do not exceed their physical constraints."""
        self.base_servo.angle = 175
        self.arm.rotate_base('right')
        self.assertEqual(self.base_servo.angle, 180)

        self.base_servo.angle = 5
        self.arm.rotate_base('left')
        self.assertEqual(self.base_servo.angle, 0)
