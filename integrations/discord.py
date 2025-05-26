import time
import logging
from utils.get_env import DC_EMAIL, DC_PASS

dc_logged_in = False

def login_discord(page):
    """Logs into Discord and saves authentication cookies."""
    global dc_logged_in
    if not dc_logged_in:
        page.goto("https://discord.com/login")
        page.fill('input[name="email"]', DC_EMAIL)
        page.fill('input[name="password"]', DC_PASS)
        page.wait_for_timeout(3000)  # Adjust wait time if needed
        page.keyboard.press("Enter")
        page.wait_for_load_state('load')
        page.wait_for_selector('text=Friends', timeout=60000)
        logging.info("Logged into Discord")
        dc_logged_in = True
    else:
        logging.info("Already logged into Discord.")

def DiscordText(page, recipient, message):
    """Sends a message to a specific recipient on Discord."""
    global dc_logged_in
    if not dc_logged_in:
        login_discord(page)
    
    page.goto("https://discord.com/channels/@me")
    page.wait_for_load_state('load')

    # Ensure the page is focused
    page.bring_to_front()
    
    # Wait for the quick switcher to be visible and then open it
    time.sleep(3)  # Slight delay to ensure page is fully loaded
    page.keyboard.press('Control+K')
    quick_switcher = page.wait_for_selector('input[aria-label="Quick switcher"]', timeout=10000)
    logging.info(f"searching for recipient {recipient}")
    quick_switcher.fill(recipient)
    time.sleep(3)  # Give time for recipient to load in quick switcher
    quick_switcher.press("Enter")
    time.sleep(3)  # Give time for recipient's chat to load

    # Wait for the message box to be ready
    message_box = page.wait_for_selector('div[role="textbox"]', timeout=10000)
    message_box.fill(message)
    message_box.press("Enter")
    logging.info(f"Message '{message}' sent to '{recipient}' on Discord!")
    time.sleep(6)  # Ensure message is sent before closing the page
    page.close()
    
    return True
