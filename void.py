import os
import re
import json
import subprocess
import logging
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from collections import Counter
from dotenv import load_dotenv
from openai import OpenAI
from unittest.mock import patch
from packs_mapping import PACKS_MAPPING

load_dotenv()
nltk.download('punkt', quiet=True)
nltk.download('averaged_perceptron_tagger', quiet=True)
nltk.download('stopwords', quiet=True)

class VOID:

    def __init__(self, open_ai_api_key, GOAL, num_GOAL, scripts_directory, memory, void_identity, material_goal):
        self.client = OpenAI(api_key=open_ai_api_key)
        self.GOAL = GOAL
        self.num_GOAL = num_GOAL
        self.scripts_directory = scripts_directory
        self.memory = memory
        self.void_identity = void_identity
        self.material_goal = material_goal

    def send_request(self, GOAL):
        full_GOAL = self.memory + "\n" + GOAL if self.memory else GOAL
        completion = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": self.void_identity},
                {"role": "user", "content": full_GOAL}
            ]
        )
        result = completion.choices[0].message.content
        return result

    def input_types(self, script_content):
        msg = f"{self.GOAL}\n\n{script_content}\n\n{self.material_goal}"
        try:
            completion = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You return accurate json responses"},
                    {"role": "user", "content": msg}
                ]
            )
            result = completion.choices[0].message.content
            parsed_result = json.loads(result)
            return parsed_result
        except Exception as e:
            print(f"Error fetching input types: {e}")
            return {}

    def format_inputs(input_type, inputs, goal):
        if not inputs:
            return ""
        inputs_text = f"{input_type.capitalize()}:\n"
        for input_item in inputs:
            file_type = input_item.split('.')[-1]
            inputs_text += f"Description: path_to_your_{input_type[:-1]}, Type={file_type}, Topic = {goal}\n"
        return inputs_text + "\n"  

    def generate_title(self, GOAL):
        words = word_tokenize(GOAL)
        words = [word for word in words if word.isalnum()]
        stop_words = set(stopwords.words('english'))
        filtered_words = [word for word in words if word.lower() not in stop_words]

        tagged_words = pos_tag(filtered_words)
        key_words = [word for word, tag in tagged_words if tag in ('NN', 'NNP')]

        word_freq = Counter(key_words)
        most_common_words = [word for word, freq in word_freq.most_common(5)]

        title = ' '.join(most_common_words)
        return title.title()

    @staticmethod
    def extract_and_divide_code(initial_version):
        code_blocks_pattern = r"```python(.*?)```"
        code_blocks = re.findall(code_blocks_pattern, initial_version, re.DOTALL)

        scripts_pattern = r"# Script (\d+).*?\n(.*?)(?=\n# Script|$)"
        
        all_scripts = []
        script_counter = 1
        
        for block in code_blocks:
            if "# Script" in block:
                scripts = re.findall(scripts_pattern, block, re.DOTALL)
                all_scripts.extend([(int(num), code.strip()) for num, code in scripts])
            else:
                all_scripts.append((script_counter, block.strip()))
                script_counter += 1

        all_scripts.sort(key=lambda x: x[0])
        return all_scripts

    def files_num(self):
        completion = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are the best coder ever exists. You only respond with numbers."},
                {"role": "user", "content": self.num_GOAL}
            ]
        )

        num_res = completion.choices[0].message.content
        digits = re.findall(r'\d+', num_res)
        digit_numbers = [int(digit) for digit in digits]
        return digit_numbers[0]

    @staticmethod
    def install_requirements(requirements, output_directory):
        os.makedirs(output_directory, exist_ok=True)
        requirements_file_path = os.path.join(output_directory, 'requirements.txt')

        with open(requirements_file_path, 'w') as requirements_file:
            for req in requirements:
                requirements_file.write(f"{req}\n")

        logging.info(f"Requirements written to {requirements_file_path}")

        for req in requirements:
            try:
                subprocess.run(["pip", "show", req], check=True, capture_output=True)
                logging.info(f"{req} is already installed")
            except subprocess.CalledProcessError:
                logging.info(f"Attempting to install {req} ...")
                try:
                    install_result = subprocess.run(["pip", "install", PACKS_MAPPING.get(req, req)], check=True, capture_output=True)
                    logging.info(f"{req} installed successfully: {install_result.stdout}")
                except subprocess.CalledProcessError as e:
                    logging.error(f"Failed to install {req}. Error: {e.stderr}")

    @staticmethod
    def execute_scripts(directory):
        """
        Executes Python scripts in the specified directory with mocked input() calls.
        Uses a default set of inputs for scripts that require user input.
        :param directory: The directory containing Python scripts to execute.
        :param default_inputs: A default list of inputs to use for mocking input() calls.
        """
        success = True
        execution_results = []
        default_inputs = ["This is a default text", "This is a default text with 123", "This is random 856 @#$"]

        for script_file in os.listdir(directory):
            if script_file.endswith(".py"):
                full_path = os.path.join(directory, script_file)
                try:
                    with open(full_path, 'r') as file:
                        script_content = file.read()

                    input_side_effects = iter(default_inputs)
                    
                    with patch('builtins.input', lambda _: next(input_side_effects, "default input")):
                        exec_globals = {}
                        exec(script_content, exec_globals)

                    execution_results.append((True, f"Script {script_file} executed successfully with mocked inputs."))
                    print(f"Script {script_file} executed successfully with mocked inputs.")
                except Exception as e:
                    execution_results.append((False, str(e)))
                    logging.error(f"Execution Error in {script_file}: {e}")
                    success = False

        return success, execution_results
