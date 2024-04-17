import os
import re
import logging
from void import VOID
import warnings

warnings.filterwarnings("ignore", category=SyntaxWarning)

OPEN_AI_API_KEY = os.getenv('OPEN_AI_API_KEY')
GOAL = os.getenv('TASK') + '. ' + os.getenv('INSTRUCTIONS')
NUM_GOAL = os.getenv('NUM_GOAL')
SCRIPTS_DIRECTORY = os.getenv('SCRIPTS_DIRECTORY')
MEMORY = os.getenv('MEMORY')
VOID_IDENTITY = os.getenv('VOID_IDENTITY')
MATERIAL_GOAL = os.getenv('MATERIAL_GOAL')

void_instance = VOID(OPEN_AI_API_KEY, GOAL, NUM_GOAL, SCRIPTS_DIRECTORY, MEMORY, VOID_IDENTITY, MATERIAL_GOAL)

PROGRAM_INITIATION = r"""

VOID PROGRAM BY:

 __    __     __     ______     ______     __         __         ______     __    __          __         ______     ______     ______    
/\ "-./  \   /\ \   /\  ___\   /\  __ \   /\ \       /\ \       /\  __ \   /\ "-./  \        /\ \       /\  __ \   /\  == \   /\  ___\   
\ \ \-./\ \  \ \ \  \ \___  \  \ \  __ \  \ \ \____  \ \ \____  \ \  __ \  \ \ \-./\ \       \ \ \____  \ \  __ \  \ \  __<   \ \___  \  
 \ \_\ \ \_\  \ \_\  \/\_____\  \ \_\ \_\  \ \_____\  \ \_____\  \ \_\ \_\  \ \_\ \ \_\       \ \_____\  \ \_\ \_\  \ \_____\  \/\_____\ 
  \/_/  \/_/   \/_/   \/_____/   \/_/\/_/   \/_____/   \/_____/   \/_/\/_/   \/_/  \/_/        \/_____/   \/_/\/_/   \/_____/   \/_____/ 
                                                                                                                                       
"""

def main():
    print(PROGRAM_INITIATION)
    TITLE = void_instance.generate_title(GOAL)
    DIR = os.path.join(SCRIPTS_DIRECTORY, TITLE)
    os.makedirs(DIR, exist_ok=True)

    log_filename = os.path.join(DIR, "execution.log")
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        handlers=[
                            logging.FileHandler(log_filename),
                            logging.StreamHandler()
                        ])

    initial_version = void_instance.send_request(GOAL)
    extracted_scripts = VOID.extract_and_divide_code(initial_version)
    requirements = set()

    for script_number, script_content in extracted_scripts:
        file_path = os.path.join(DIR, f'main{script_number}.py')
        with open(file_path, 'w') as file:
            file.write(script_content)
            logging.info(f"Script file created: {file_path}")
            requirements.update(re.findall(r"(?m)^(?:from\s+(\S+)|import\s+(\S+))(?=\s|$)", script_content))

        input_types_result = void_instance.input_types(script_content)

        inputs_text = ""
        for input_type in ['images', 'videos', 'audio']:
            formatted_section = VOID.format_inputs(input_type, input_types_result.get(input_type, []), GOAL)
            if formatted_section:
                inputs_text += formatted_section

        if inputs_text:
            inputs_filename = os.path.join(DIR, f'inputs{script_number}.txt')
            with open(inputs_filename, 'a') as inputs_file:
                inputs_file.write(inputs_text)
                logging.info(f"Inputs file created: {inputs_filename}")

    requirements = {pkg.split('.')[0] for pkg_tuple in requirements for pkg in pkg_tuple if pkg}
    VOID.install_requirements(requirements, DIR)

    success, execution_results = VOID.execute_scripts(DIR)
    while not success:
        logging.info("Attempting to fix errors and re-execute ...")
        void_instance.memory += "\nFix the above errors."
        corrected_version = void_instance.send_request(GOAL)
        extracted_scripts = VOID.extract_and_divide_code(corrected_version)

        for filename in os.listdir(DIR):
            file_path = os.path.join(DIR, filename)
            if file_path.endswith(".py"):
                os.remove(file_path)
                logging.info(f"Removed file: {file_path}")

        for script_number, script_content in extracted_scripts:
            file_path = os.path.join(DIR, f'main{script_number}.py')
            with open(file_path, 'w') as file:
                file.write(script_content)
                logging.info(f"Script file recreated: {file_path}")

        success, execution_results = VOID.execute_scripts(DIR)
        if success:
            break

    for success, output in execution_results:
        if success:
            logging.info(f"Execution Output:\n{output}")
        else:
            logging.error(f"Execution Output:\n{output}")

if __name__ == "__main__":
    main()
