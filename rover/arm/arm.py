from time import sleep


class RobotArm:
    def __init__(self,
                 gripper_servo,
                 wrist_roll_servo,
                 wrist_pitch_servo,
                 elbow_servo,
                 shoulder_servo,
                 base_servo,
                 step=5
             ):
        """Initialize the robot arm with a list of six servos."""
        self.gripper_servo = gripper_servo
        self.wrist_roll_servo = wrist_roll_servo
        self.wrist_pitch_servo = wrist_pitch_servo
        self.elbow_servo = elbow_servo
        self.shoulder_servo = shoulder_servo
        self.base_servo = base_servo

        self.step = step

    def go_to_starting_position(self):
        """Move the arm to the starting position."""
        self.gripper_servo.angle = 0
        self.wrist_roll_servo.angle = 0
        sleep(.5)
        self.wrist_pitch_servo.angle = 0
        self.elbow_servo.angle = 0
        sleep(.5)
        self.shoulder_servo.angle = 110
        sleep(.5)
        self.base_servo.angle = 0
        sleep(.5)

    def operate_gripper(self, action):
        """Open or close the gripper."""
        print("OPERATING GRIPPER", action)
        self.gripper_servo.angle = 0 if action == 'close' else 180


    def roll_wrist(self, direction):
        """Roll the wrist of the arm clockwise or counterclockwise."""
        print("ROLLING WRIST", direction)
        increment = self.determine_step(direction != 'clockwise')
        self.increment_servo_angle(self.wrist_roll_servo, increment)


    def pitch_wrist(self, direction):
        """Pitch the wrist of the arm up or down."""
        print("PITCHING WRIST", direction)
        increment = self.determine_step(direction != 'up')
        self.increment_servo_angle(self.wrist_pitch_servo, increment)


    def move_elbow(self, direction):
        """Adjust the elbow of the arm."""
        print("MOVING ELBOW", direction)
        increment = self.determine_step(direction != 'bend')
        self.increment_servo_angle(self.elbow_servo, increment)


    def move_shoulder(self, direction):
        """Move the shoulder of the arm up or down."""
        print("MOVING SHOULDER", direction)
        increment = self.determine_step(direction != 'up')
        self.increment_servo_angle(self.shoulder_servo, increment)


    def rotate_base(self, direction):
        """Rotate the base of the arm left or right."""
        print("MOVING BASE", direction)
        increment = self.determine_step(direction != 'right')
        self.increment_servo_angle(self.base_servo, increment)


    def determine_step(self, should_negate):
        return -self.step if should_negate else self.step


    @staticmethod
    def increment_servo_angle(servo, increment):
        """Increment the angle of the given servo by the given amount."""
        print("INCREMENTING ANGLE", servo.angle, increment)
        new_angle = max(0, min(180, servo.angle + increment))
        print("NEW ANGLE", new_angle)
        servo.angle = new_angle
        print("ACTUAL NEW ANGLE", servo.angle)
        print()


