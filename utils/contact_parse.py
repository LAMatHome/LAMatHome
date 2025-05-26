import logging
from contacts import contacts
import string

def get_contact_name(integration, recipient):
    """Get the actual name from the recipient or its nickname for the given integration."""
    if integration not in contacts:
        logging.error(f"Integration {integration} not found.")
        return None

    for contact in contacts[integration]:
        if recipient.lower() == contact["name"].lower():
            return contact["name"]
        if recipient.lower() in [nickname.lower() for nickname in contact["nicknames"]]:
            return contact["name"]
    return None

def process_message(words):
    integration = words[0].strip('.,!?:;"').lower()
    recipient = None
    action = None
    message = None
    actions_list = ["site", "google", "youtube", "gmail", "amazon", "volume", "run", "media", "power", "terminate"]

    if integration in ['telegram', 'discord', 'facebook']:
        combined_recipient = f"{words[1].strip(string.punctuation).lower()} {words[2].strip(string.punctuation).lower()}"
        name = get_contact_name(integration, combined_recipient)
        
        if name:
            recipient = name
            message = ' '.join(words[3:]).strip()
        else:
            single_recipient = words[1].strip(string.punctuation).lower()
            name = get_contact_name(integration, single_recipient)
            if name:
                recipient = name
                message = ' '.join(words[2:]).strip()
            else:
                if single_recipient in actions_list:
                    action = single_recipient
                else:
                    recipient = single_recipient
                message = ' '.join(words[2:]).strip()
    else:
        action = words[1].strip('.,!?:;"').lower()
        message = ' '.join(words[2:]).strip()

    return integration, recipient, action, message