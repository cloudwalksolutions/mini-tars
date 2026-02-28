import os
from openai import OpenAI



class GenAI:
    def __init__(self, api_key=None):
        self.client = OpenAI(api_key=api_key)
        self.messages = []
        self.add_system_instruction('You are a little rover named the Cloud Rover 1.0')
        self.add_system_instruction('Do not make any assumptions about what you are seeing.')


    def add_user_input(self, input):
        instruction = {"role": "user", "content": input}
        self.messages.append(instruction)


    def add_system_instruction(self, input):
        instruction = {"role": "system", "content": input}
        self.messages.append(instruction)


    def add_assistant_response(self, input):
        instruction = {"role": "assistant", "content": input}
        self.messages.append(instruction)


    def chat(self, message, extra_context={}):
        for k, v in extra_context.items():
            self.add_system_instruction(f'{k}: {v}')

        self.add_user_input(message)

        response = self.ask_gpt(self.messages)

        self.add_assistant_response(response)
        return response


    def ask_gpt(self, messages):
        try:
            completion = self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=messages
            )
            response = completion.choices[0].message.content
            return response
        except Exception as e:
            print(e)
            return e


