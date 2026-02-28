import pigpio
import time

# Initialize pigpio
pi = pigpio.pi('soft', 8888)

# Define servo GPIO pin
servo_pin = 14  # Change as per your connection

# Function to set servo angle
def set_servo_angle(angle):
    # Convert angle to PWM duty cycle
    duty_cycle = int((angle * 2000 / 180) + 500)  # Adjust conversion based on your servo specs
    pi.set_servo_pulsewidth(servo_pin, duty_cycle)

try:
    while True:
        # Set servo to 0 degrees
        set_servo_angle(0)
        time.sleep(1)
        # Set servo to 90 degrees
        set_servo_angle(90)
        time.sleep(1)
        # Set servo to 180 degrees
        set_servo_angle(180)
        time.sleep(1)

except KeyboardInterrupt:
    # Clean up
    pi.set_servo_pulsewidth(servo_pin, 0)  # Turn off servo
    pi.stop()

