import os
import json
import logging
import coloredlogs
import threading
from integrations import lam_at_home
from datetime import datetime, timezone
from utils import config, get_env, rabbit_hole, splash_screen, new_ui, llm_parse, task_executor, journal
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

stop_event = threading.Event()
    
def process_utterance(journal_entry, journal: journal.Journal, playwright_context):
    if isinstance(journal_entry, str):
        utterance = journal_entry
    else:
        utterance = journal_entry['utterance']['prompt']
    logging.info(f"Prompt: {utterance}")

    entry, promptParsed = None, None
    try:
        if utterance:
            # split prompt into tasks
            promptParsed = llm_parse.LLMParse(utterance, journal.get_interactions())
            tasks = promptParsed.split("&&")

            # iterate through tasks and execute each sequentially
            for task in tasks:
                if task != "x":
                    logging.info(f"Task: {task}")
                    task_executor.execute_task(playwright_context, task)
        else:
            logging.info("No prompt found in entry, skipping LLM Parse and task execution.")

        # Append the completed interaction to the journal
        entry = journal.add_entry(journal_entry, llm_response=promptParsed)

        if config.config['lamathomesave_isenabled'] and entry.type in config.config['lamathomesave_types']:
            lam_at_home.save(journal, entry)

    except PlaywrightTimeoutError:
        logging.error("Playwright timed out while waiting for response.")

    except Exception as e:
        logging.error(f"An error occurred: {e}")

def main():
    try:
        print(splash_screen.colored_splash)
        logging.info("LAMatHome is starting...")

        # create cache directory if it doesn't exist
        if not os.path.exists(config.config['cache_dir']):
            os.makedirs(config.config['cache_dir'])

        # Ensure state.json exists and is valid
        state_file = os.path.join(config.config['cache_dir'], config.config['state_file'])
        if not os.path.exists(state_file) or os.stat(state_file).st_size == 0:
            with open(state_file, 'w') as f:
                json.dump({}, f)

        # Initialize journal for storing rolling transcript
        user_journal = journal.Journal(max_entries=config.config['rolling_transcript_size'])

        with sync_playwright() as p:
            # Use firefox for full headless
            browser = p.firefox.launch(headless=False)
            context = browser.new_context(storage_state=state_file)  # Use state to stay logged in

            user, assistant = None, None
            if get_env.RH_ACCESS_TOKEN:
                # fetch rabbit hole user profile
                profile = rabbit_hole.fetch_user_profile()
                user = profile.get('name')
                assistant = profile.get('assistantName')
            
            if config.config["mode"] == "rabbit":
                current_time_iso = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                logging.info(f"Welcome {user}! LAMatHome is now listening for journal entries posted by {assistant}")
                for journal_entry in rabbit_hole.journal_entries_generator(current_time_iso):
                    if stop_event.is_set():
                        break
                    process_utterance(journal_entry, user_journal, context)
            
            elif config.config["mode"] == "cli":
                logging.info("Entering interactive mode...")
                while not stop_event.is_set():
                    user_input = input(f"{user}@LAMatHome> " if user else "LAMatHome> ")
                    process_utterance(user_input, user_journal, context)

            else:
                logging.error("Invalid mode specified in config.json")

    except KeyboardInterrupt:
        logging.info("Program terminated by user")
    finally:
        lam_at_home.terminate()

if __name__ == "__main__":
    # Configure logging and run LAMatHome
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    coloredlogs.install(
        level='INFO', 
        fmt='%(asctime)s - %(levelname)s - %(message)s', 
        datefmt='%Y-%m-%d %H:%M:%S', 
        field_styles={'asctime': {'color': 'white'}}
    )
    
    new_ui.popup()