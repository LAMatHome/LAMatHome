from interpreter import interpreter
import logging
from utils import config
from utils.get_env import OI_API_KEY

# set api base url based on config (valid options: groq, openai, or user set url)
if config.config.get("openinterpreter_llm_api_base") in ["groq", "openai"]:
    if config.config.get("openinterpreter_llm_api_base") == "groq":
        interpreter.llm.api_base = "https://api.groq.com/openai/v1"
    elif config.config.get("openinterpreter_llm_api_base") == "openai":
        interpreter.llm.api_base = "https://api.openai.com/v1/models"
else:
    interpreter.llm.api_base = config.config.get("openinterpreter_llm_api_base")

if config.config.get("openinterpreter_verbose_mode_isenabled") == "true":
    interpreter.verbose = True
elif config.config.get("openinterpreter_verbose_mode_isenabled") == "false":
    interpreter.verbose = False
else:
    logging.error("Invalid value for openinterpreter_verbose_mode_isenabled in config. Defaulting to true")
    interpreter.verbose = True

# set the rest of the OI values
interpreter.auto_run = config.config.get("openinterpreter_auto_run_isenabled")
interpreter.llm.api_key = OI_API_KEY
interpreter.llm.model = config.config.get("openinterpreter_llm_model")
interpreter.llm.temperature = config.config.get("openinterpreter_llm_temperature")

# Run openinterpreter based on task from llm_parse.py
def openinterpretercall(task):
    interpreter.chat(task)
    logging.info(f"Sent to OpenInterpreter: {task}")
    # logging.info(f"OpenInterpreter response: {interpreter.response}")