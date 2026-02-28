import unittest
from unittest.mock import MagicMock, patch

import asyncio
from gpiozero import LED
import speech_recognition as sr

from .audio import AudioSensor


class TestAudioSensor(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.listen_duration = 5
        self.light = MagicMock(spec=LED)
        self.recognizer = MagicMock()
        self.microphone = MagicMock()
        self.gen_ai = MagicMock()
        self.tts = MagicMock()
        self.mixer = MagicMock()
        self.mixer.music.return_value = MagicMock()
        self.mixer.music.get_busy.return_value = False
        self.audio_sensor = AudioSensor(
            light=self.light,
            listen_duration=self.listen_duration,
            mixer=self.mixer,
            recognizer=self.recognizer,
            microphone=self.microphone,
            gen_ai=self.gen_ai,
        )


    def test_transcribe_successful(self):
        self.recognizer.recognize_google.return_value = "hello world"

        result = self.audio_sensor.transcribe('audio_data')

        self.recognizer.recognize_google.assert_called_once_with('audio_data')
        self.assertEqual(result, "hello world")


    def test_transcribe_unknown_value_error(self):
        self.recognizer.recognize_google.side_effect = sr.UnknownValueError()
        result = self.audio_sensor.transcribe('audio_data')
        self.assertIsNone(result)


    def test_transcribe_request_error(self):
        self.recognizer.recognize_google.side_effect = sr.RequestError()
        result = self.audio_sensor.transcribe('audio_data')
        self.assertIsNone(result)


    def test_play_audio(self):
        filename = "test_audio.mp3"
        self.mixer.music.get_busy.return_value = False

        self.audio_sensor.play_audio(filename)

        self.mixer.init.assert_called_once()
        self.mixer.music.load.assert_called_once_with(filename)
        self.mixer.music.play.assert_called_once()
        self.assertFalse(self.mixer.music.get_busy())


    @patch('rover.sensors.audio.gTTS')
    @patch('rover.sensors.audio.AudioSensor.play_audio')
    def test_text_to_speech(self, mock_play_audio, mock_gtts):
        mock_tts = MagicMock()
        mock_gtts.return_value = mock_tts

        text = "Hello, world!"
        filename = "hello.mp3"
        self.audio_sensor.text_to_speech(text, filename)

        mock_gtts.assert_called_once_with(text=text, lang='en')
        mock_tts.save.assert_called_once_with(filename)
        mock_play_audio.assert_called_once_with(filename)


    def test_listen(self):
        self.recognizer.listen.return_value = 'audio_data'

        result = self.audio_sensor.listen()

        self.recognizer.adjust_for_ambient_noise.assert_called_once()
        self.recognizer.listen.assert_called_once()
        self.assertEqual(result, 'audio_data')


    def test_empty_stop_listening(self):
        self.assertFalse(self.audio_sensor.is_active())
        self.audio_sensor.stop_listening()
        self.assertFalse(self.audio_sensor.is_active())


    @patch('rover.sensors.audio.AudioSensor.transcribe')
    @patch('rover.sensors.audio.AudioSensor.listen')
    async def test_start_listening(self, listen, transcribe):
        listen.return_value = 'audio_data'
        transcribe.return_value = 'hello world'
        expected_output = "Hello to you too!"
        self.gen_ai.chat.return_value = expected_output
        stop_event = asyncio.Event()

        listen_task = asyncio.create_task(self.audio_sensor.start_listening(stop_event))

        await asyncio.sleep(.1)
        self.assertTrue(self.audio_sensor.is_active())
        self.audio_sensor.stop_listening()
        await listen_task
        self.light.blink.assert_called_once()
        self.light.on.assert_called_once()
        self.assertFalse(self.audio_sensor.is_active())
        self.assertEqual(len(self.audio_sensor.recordings), 1,)
        self.assertEqual(len(self.audio_sensor.transcriptions), 1,)
        self.assertEqual(self.audio_sensor.recordings[0], 'audio_data')
        self.assertEqual(self.audio_sensor.transcriptions[0], 'hello world')

        response = self.audio_sensor.respond_to_audio()
        self.assertEqual(response, expected_output)
        self.assertEqual(len(self.audio_sensor.recordings), 0)
        self.assertEqual(len(self.audio_sensor.transcriptions), 0)


