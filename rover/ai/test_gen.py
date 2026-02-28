import unittest
from unittest.mock import patch, MagicMock

from .gen import GenAI


class TestGenAI(unittest.TestCase):
    def setUp(self):
        self.basic_instructions = [
            {"role": "system", "content": 'You are a little rover named the Cloud Rover 1.0'},
            {"role": "system", "content": 'Do not make any assumptions about what you are seeing.'},
        ]
        self.gen_ai = GenAI(api_key="fake_api_key")
        self.assertEqual(self.gen_ai.messages, self.basic_instructions)


    def test_add_instructions(self):
        input = "hey"
        self.gen_ai.add_user_input(input)
        self.assertEqual(self.gen_ai.messages[-1], {"role": "user", "content": input})

        self.gen_ai.add_system_instruction(input)
        self.assertEqual(self.gen_ai.messages[-1], {"role": "system", "content": input})

        self.gen_ai.add_assistant_response(input)
        self.assertEqual(self.gen_ai.messages[-1], {"role": "assistant", "content": input})


    @patch('rover.ai.gen.GenAI.ask_gpt')
    def test_chat(self, mock_ask_gpt):
        mock_ask_gpt.return_value = 'hey hey'
        message = "hey"
        rover_status = {
            "gps": "37.7749° N, 122.4194° W",
            "temperature": "22°C",
            "humidity": "78%",
        }
        expected_messages = [{
                'role': 'system',
                'content': 'gps: 37.7749° N, 122.4194° W'
            }, {
                'role': 'system',
                'content': 'temperature: 22°C'
            }, {
                'role': 'system',
                'content': 'humidity: 78%'
            }, {
                'role': 'user',
                'content': 'hey'
            }]

        response = self.gen_ai.chat(message, rover_status)

        context_messages = [x for x in self.gen_ai.messages if x['role'] != 'assistant' and x not in self.basic_instructions]
        self.assertEqual(context_messages, expected_messages)
        self.assertEqual(response, "hey hey")
        self.assertEqual(self.gen_ai.messages[-1], {
            'role': 'assistant',
            'content': response
        })

