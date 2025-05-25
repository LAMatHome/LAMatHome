import sys
import time
import logging
import requests
from datetime import datetime, timezone
from .config import config
from .get_env import RH_ACCESS_TOKEN

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# rabbit hole base endpoint
BASE_URL = f"https://{config['host']}/apis"

# headers for the requests made to rabbit hole
headers = {
    "host": config["host"],
    "sec-ch-ua": "\"Google Chrome\";v=\"125\", \"Chromium\";v=\"125\", \"Not.A/Brand\";v=\"24\"",
    "sec-ch-ua-platform": "Windows",
    "sec-ch-ua-mobile": "?0",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/",
    "content-type": "application/json",
    "Accept": "*/*",
    "Sec-Fetch-Site": "same-origin",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Dest": "empty",
}

error_count = 0  # sequential error count
def handle_request_errors(func):  
    '''
    Decorator to handle web request errors.
    '''
    def wrapper(*args, **kwargs):
        global error_count
        try:
            response = func(*args, **kwargs)
            response.raise_for_status()
            error_count = 0
            return response.json()
        except requests.exceptions.HTTPError as e:
            error_count += 1
            logging.error(f"Server error: {e} when calling {func.__name__}")
            if error_count == config["rabbithole_api_max_retry"]:
                logging.error("Max retries exceeded. Terminating...")
                sys.exit()
        except requests.exceptions.RequestException as e:
            logging.error(f"Request error: {e}")
        return None
    return wrapper


@handle_request_errors
def fetch_user_profile():
    '''
    Fetches the profile for the given user.
    '''
    url = f"{BASE_URL}/fetchUserProfile"
    params = {"accessToken": RH_ACCESS_TOKEN}
    return requests.get(url, headers=headers, params=params)


@handle_request_errors
def update_user_profile(profile=None):
    '''
    Updates profile for the given user.
    '''
    url = f"{BASE_URL}/updateUserProfile"
    body = {"accessToken": RH_ACCESS_TOKEN, "profile": profile}
    return requests.patch(url, headers=headers, json=body)


@handle_request_errors
def fetch_user_entry_resource(urls):
    '''
    Fetches the resources for the given entry id 
    '''
    url = f"{BASE_URL}/fetchJournalEntryResources"
    params = {"accessToken": RH_ACCESS_TOKEN, "urls": urls}
    return requests.get(url, headers=headers, params=params)


@handle_request_errors
def fetch_user_journal():
    '''
    Fetches all journal entries for the given user.
    '''
    url = f"{BASE_URL}/fetchUserJournal"
    body = {"accessToken": RH_ACCESS_TOKEN}
    return requests.post(url, headers=headers, json=body)


def is_valid_iso_format(timestamp):
    '''
    Check if the given timestamp is in ISO format.
    '''
    try:
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return True
    except ValueError:
        return False


def get_journals(before=None, after=None):
    '''
    Get journal entries with optional filtering by iso timestamps.
    '''
    if before and not is_valid_iso_format(before):
        raise ValueError("Invalid 'before' timestamp format")
    if after and not is_valid_iso_format(after):
        raise ValueError("Invalid 'after' timestamp format")
    if before and after and before <= after:
        raise ValueError("'before' timestamp must be after 'after' timestamp")

    responseDict = fetch_user_journal()
    if not responseDict:
        return []

    journalEntries = responseDict.get('journal', {}).get('entries', [])
    if before:
        journalEntries = [entry for entry in journalEntries if entry["createdOn"] < before]
    if after:
        journalEntries = [entry for entry in journalEntries if entry["createdOn"] > after]

    return journalEntries


def journal_entries_generator(after_timestamp, intention_filter=None):
    '''
    Generator to get all journal entries in real-time after the given timestamp.
    '''
    while True:
        new_entries = get_journals(after=after_timestamp)
        if new_entries:
            for entry in new_entries:
                if intention_filter == None or entry['utterance']['intention'] in intention_filter:
                    yield entry
            # Update the after_timestamp to the latest entry's createdOn timestamp
            # ensures that we only get new entries in the next iteration
            after_timestamp = new_entries[-1]['createdOn']
        else:
            # If no new entries, wait for a while before checking again
            time.sleep(config["rabbithole_api_sleep_time"])


if __name__ == "__main__":
    # Example usage of the journal_entries_generator
    # filtering only for journals marked with conversation intent
    # Assuming the initial after_timestamp is the current time in ISO format
    initial_timestamp = currentTimeIso = datetime.now(timezone.utc).isoformat() + 'Z'
    generator = journal_entries_generator(initial_timestamp, ["CONVERSATION"])

    # Print the journal entries as they come in real-time
    for entry in generator:
        print(entry)
