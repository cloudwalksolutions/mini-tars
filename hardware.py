from time import sleep
from signal import pause
from gpiozero import AngularServo
from gtts import gTTS
import pygame
import speech_recognition as sr
from picamera2 import Picamera2
from picamera2.previews.null_preview import NullPreview
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import ssd1306

from rover.arm.arm import RobotArm
from rover.sensors.gps import GPSTracker
from rover.servers.pins import *


def speech_to_text():
  recognizer = sr.Recognizer()
  exit_phrase = "goodbye world"

  try:
    with sr.Microphone() as source:
      recognizer.adjust_for_ambient_noise(source)
      print(f"Listening... Speak into the microphone. Say '{exit_phrase}' or press Ctrl+C to stop.")

      while True:
        try:
          audio_data = recognizer.listen(source)
          print("Transcribing...")

          text = recognizer.recognize_google(audio_data)
          print("Transcribed Text: " + text)
          return text

          if exit_phrase.lower() in text.lower():
            print("Exit phrase detected, stopping...")
            break

        except sr.UnknownValueError:
          print("Could not understand audio. Please try again.")
        except sr.RequestError as e:
          print(f"Could not request results; {e}")

  except KeyboardInterrupt:
    print("\nManual interruption detected. Exiting...")


def play_audio(filename):
  print("Playing back audio...")
  pygame.mixer.init()
  pygame.mixer.music.load(filename)
  pygame.mixer.music.play()

  while pygame.mixer.music.get_busy():
    continue


def text_to_speech(text, filename):
  print("Translating text to speech..")
  tts = gTTS(text=text, lang='en')
  tts.save(filename)


def test_audio():
  print("Recording audio...")
  filename = '/tmp/temp_audio.mp3'
  text = speech_to_text()
  text_to_speech(text, filename)
  play_audio(filename)


def test_gps():
  print("Getting GPS coordinates...")
  serial_port = "/dev/ttyAMA0"
  gps_tracker = GPSTracker(serial_port)
  location = gps_tracker.location()
  if location:
    print(f"Lat: {location.latitude}, Long: {location.longitude}")
  else:
    print("No location data found")


def test_picture():
  picam2 = Picamera2()
  picam2.start_preview(NullPreview())
  picam2.start_and_capture_file("test.jpg")


def test_video():
  picam2 = Picamera2()
  picam2.start_and_record_video("test.mp4", duration=5)


def test_servo(servo, angles):
  for angle in angles:
    servo.angle = angle
    sleep(2)


def test_arm():

  servos = [
    AngularServo(ARM_SERVO_PIN_1, min_angle=0, max_angle=90),
    AngularServo(ARM_SERVO_PIN_2, min_angle=0, max_angle=180),
    AngularServo(ARM_SERVO_PIN_3, min_angle=0, max_angle=180),
    AngularServo(ARM_SERVO_PIN_4, min_angle=0, max_angle=180),
    AngularServo(ARM_SERVO_PIN_5, initial_angle=110, min_angle=0, max_angle=180),
    AngularServo(ARM_SERVO_PIN_6, min_angle=0, max_angle=180),
  ]

  arm = RobotArm(
    gripper_servo=servos[0],
    wrist_roll_servo=servos[1],
    wrist_pitch_servo=servos[2],
    elbow_servo=servos[3],
    shoulder_servo=servos[4],
    base_servo=servos[5],
  )

  test_servo(servos[0], [90, 0, 90,  0])
  test_servo(servos[1], [180, 90, 0, 90, 180, 90, 0])
  test_servo(servos[2], [180, 90, 0, 90, 180, 90, 0])
  test_servo(servos[3], [180, 90, 0, 90, 180, 90, 0])
  test_servo(servos[4], [80, 110, 140, 110])
  test_servo(servos[5], [180, 90, 0, 90, 180, 90, 0])

#    arm.increment_servo_angle(servos[i], 5)
#    s.angle = 60
#    sleep(1)

#    arm.increment_servo_angle(servos[i], -5)
#    s.angle = 70
#    sleep(1)

#  sleep(1)
#  arm.operate_gripper('open')
#  sleep(1)
#  arm.operate_gripper('close')

#  sleep(1)
#  arm.roll_wrist('clockwise')
#  sleep(1)
#  arm.roll_wrist('counterclockwise')

#  sleep(1)
#  arm.pitch_wrist('up')
#  sleep(1)
#  arm.pitch_wrist('down')

#  sleep(1)
#  arm.move_elbow('bend')
#  sleep(1)
#  arm.move_elbow('extend')

#  sleep(1)
#  arm.move_shoulder('up')
#  sleep(1)
#  arm.move_shoulder('down')

#  sleep(1)
#  arm.rotate_base('left')
#  sleep(1)
#  arm.rotate_base('right')
#  sleep(1)

  arm.go_to_starting_position()

def test_display():
  serial = i2c(port=1, address=0x3C)
  device = ssd1306(serial)

  with canvas(device) as draw:
    draw.rectangle(device.bounding_box, outline="white", fill="black")
    draw.text((0, 0), "Cloud Rover", fill="white")
    draw.text((10, 15), 'Distance: .3m', fill="white")


def main():

  while True:
    msg = "OPTIONS\n" + \
          "-------\n" + \
          "a - audio record/playback\n" + \
          "s - servo\n" + \
          "o - oled display\n" + \
          "g - GPS coordinates\n" + \
          "p - take picture\n" + \
          "v - take video\n" + \
          "\nEnter command: "

    user_input = input(msg)
    if not user_input:
      continue

    user_input = user_input.lower()

    if user_input == "a":
      test_audio()
    elif user_input == "s":
      test_arm()
    elif user_input == "o":
      test_display()
    elif user_input == "g":
      test_gps()
    elif user_input == "p":
      test_picture()
    elif user_input == "v":
      test_video()


if __name__ == "__main__":
  try:
    main()
  except Exception as e:
    print("Something went wrong:", e)

