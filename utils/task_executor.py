import logging
from utils import config, helpers
from integrations import browser, computer, discord, facebook, google, lam_at_home, open_interpreter, telegram
from utils import contact_parse

def execute_task(context, text):
    words = text.split()
    if len(words) < 3:
        logging.error("Command did not provide enough parameters.")
        return
    
    integration, recipient, action, message = contact_parse.process_message(words)
    
    if integration == "browser":
        if not config.config["browser_isenabled"]:
            helpers.log_disabled_integration("Browser")
            return
        
        if action in ["site", "google", "youtube", "gmail", "amazon"]:
            search = message.strip()

            if action == "site":
                if config.config["browsersite_isenabled"]:
                    browser.BrowserSite(search)
                else:
                    helpers.log_disabled_integration("BrowserSite")
            elif action == "google":
                if config.config["browsergoogle_isenabled"]:
                    browser.BrowserGoogle(search)
                else:
                    helpers.log_disabled_integration("BrowserGoogle")
            elif action == "youtube":
                if config.config["browseryoutube_isenabled"]:
                    browser.BrowserYoutube(search)
                else:
                    helpers.log_disabled_integration("BrowserYoutube")
            elif action == "gmail":
                if config.config["browsergmail_isenabled"]:
                    browser.BrowserGmail(search)
                else:
                    helpers.log_disabled_integration("BrowserGmail")
            elif action == "amazon":
                if config.config["browseramazon_isenabled"]:
                    browser.BrowserAmazon(search)
                else:
                    helpers.log_disabled_integration("BrowserAmazon")
        else:
            logging.error("Unknown Browser command or the integration is not enabled.")

    elif integration == "computer":
        if not config.config["computer_isenabled"]:
            helpers.log_disabled_integration("Computer")
            return

        if action in ["volume", "run", "media", "power"]:
            if action == "volume":
                if config.config["computervolume_isenabled"]:
                    computer.ComputerVolume(text)
                    return
                else:
                    helpers.log_disabled_integration("ComputerVolume")
            elif action == "run":
                if config.config["computerrun_isenabled"]:
                    computer.ComputerRun(text)
                    return
                else:
                    helpers.log_disabled_integration("ComputerSite")
            elif action == "media":
                if config.config["computermedia_isenabled"]:
                    computer.ComputerMedia(text)
                    return
                else:
                    helpers.log_disabled_integration("ComputerMedia")
            elif action == "power":
                if config.config["computerpower_isenabled"]:
                    computer.ComputerPower(text)
                    return
                else:
                    helpers.log_disabled_integration("ComputerPower")
        else:
            logging.error("Unknown Computer command or the integration is not enabled.")

    elif integration == "discord":
        page = context.new_page()  # Open a new page
        if config.config["discord_isenabled"]:
            if config.config["discordtext_isenabled"]:
                discord.DiscordText(page, recipient, message)
                return
            else:
                helpers.log_disabled_integration("DiscordText")
        else:
            helpers.log_disabled_integration("Discord")

    elif integration == "facebook":
        page = context.new_page()  # Open a new page
        if config.config["facebook_isenabled"]:
            if config.config["facebooktext_isenabled"]:
                facebook.FacebookText(page, recipient, message)
                return
            else:
                helpers.log_disabled_integration("FacebookText")
        else:
            helpers.log_disabled_integration("Facebook")

    elif integration == "google":
        page = context.new_page()  # Open a new page
        if config.config["google_isenabled"]:
            if config.config["googlehome_isenabled"]:
                google.GoogleHome(page, message)
                return
            else:
                helpers.log_disabled_integration("GoogleHome")
        else:
            helpers.log_disabled_integration("Google")

    elif integration == "lamathome":
        if not config.config["lamathome_isenabled"]:
            helpers.log_disabled_integration("LAMatHome")
            return

        if action == "terminate":
            if config.config["lamathometerminate_isenabled"]:
                lam_at_home.terminate()
            else:
                logging.error("Unknown LAMatHome command or the integration is not enabled.")
    
    elif integration == "openinterpreter":
        if not config.config["openinterpreter_isenabled"]:
            helpers.log_disabled_integration("OpenInterpreter")
            return

        if config.config["openinterpreter_isenabled"]:
            message_OI = ' '.join(words[1:]).strip()
            open_interpreter.openinterpretercall(message_OI)
        else:
            logging.error("Unknown OpenInterpreter command or the integration is not enabled.")

    elif integration == "telegram":
        if config.config["telegram_isenabled"]:
            if config.config["telegramtext_isenabled"]:
                telegram.TelegramText(context, recipient, message)
                return
            else:
                helpers.log_disabled_integration("TelegramText")
        else:
            helpers.log_disabled_integration("Telegram")

    else:
        logging.error("Unknown command type.")