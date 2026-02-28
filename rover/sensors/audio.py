import os
import asyncio
import speech_recognition as sr
from gtts import gTTS
import pygame


os.environ['SDL_AUDIODRIVER'] = 'pulseaudio'


class AudioSensor:
    def __init__(self,
                 light=None,
                 listen_duration=5,
                 recognizer=None,
                 microphone=None,
                 mixer=None,
                 gen_ai=None):
        self.light = light
        self.listen_duration = listen_duration
        self.recognizer = recognizer or sr.Recognizer()
        self.microphone = microphone or sr.Microphone()
        self.mixer = mixer or pygame.mixer
        self.gen_ai = gen_ai

        self.recordings = []
        self.transcriptions = []
        self.stop_listening_event = None


    def is_active(self):
        return self.stop_listening_event and not self.stop_listening_event.is_set()


    async def start_listening(self, stop_event):
        print("STARTING TO LISTEN FOR AUDIO")
        self.stop_listening_event = stop_event

        if self.light is not None:
            self.light.blink()

        while not stop_event.is_set():
            print("LISTENING FOR AUDIO")
            recording = await asyncio.to_thread(self.listen)
            if recording is not None:
                self.recordings.append(recording)

                transcription = self.transcribe(recording)
                if transcription is not None:
                    self.transcriptions.append(transcription)

            print(f"SLEEPING DURING LISTEN FOR {self.listen_duration} SECONDS")
            await asyncio.sleep(self.listen_duration)
            print(f"DONE SLEEPING DURING LISTEN")

        if self.light is not None:
            self.light.on()


    def listen(self):
        print("START LISTEN")
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
            audio = self.recognizer.listen(source, timeout=self.listen_duration)
            print("END LISTEN")
            return audio


    def transcribe(self, audio_data):
        try:
            print("TRANSCRIBING AUDIO")
            text = self.recognizer.recognize_google(audio_data)
            print("TRANSCRIBED INTO:", text)
            return text
        except sr.UnknownValueError:
            print("Could not understand audio. Please try again.")
        except sr.RequestError as e:
            print(f"Could not request results; {e}")


    def stop_listening(self):
        if self.stop_listening_event is not None:
            self.stop_listening_event.set()


    def text_to_speech(self, text, filename):
        print("TRANSLATING TEXT TO SPEECH: ", text)
        tts = gTTS(text=text, lang='en')
        tts.save(filename)
        self.play_audio(filename)


    def play_audio(self, filename):
        if self.mixer is not None:
            print("PLAYING AUDIO")
            self.mixer.init()
            self.mixer.music.load(filename)
            self.mixer.music.play()

            while self.mixer.music.get_busy():
                continue


    def respond_to_audio(self, context=None):
        print("RESPONDING TO AUDIO WITH CONTEXT: ", context)
        if len(self.transcriptions) > 0:
            if self.gen_ai is not None:
                response = self.gen_ai.chat(' '.join(self.transcriptions), context)
            else:
                response = 'No AI detected'
        else:
            response = 'No audio recorded'

        self.text_to_speech(response, '/tmp/response.mp3')

        self.recordings = []
        self.transcriptions = []
        return response


