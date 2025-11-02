# Description:
# DEBUGGING SCRIPT (Phase 3)
# This script finds the __NEXT_DATA__ JSON and prints the keys
# inside `pageProps` to find the real name of the boss list.

import requests
import json
from bs4 import BeautifulSoup
from discord_webhook import DiscordWebhook, DiscordEmbed
import os
import sys

BOSS_TRACKER_URL = "https://www.exevopan.com/bosses"

def scrape_top_bosses():
    """
    Attempts to scrape the Exevo Pan boss tracker.
    Currently in DEBUG mode to find JSON keys.
    """
    print(f"Attempting to scrape boss data from: {BOSS_TRACKER_URL}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    try:
        session = requests.Session()
        response = session.get(BOSS_TRACKER_URL, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})
        
        if not next_data_script:
            return None, "Error: Could not find the `__NEXT_DATA__` script tag."

        data = json.loads(next_data_script.string)

        # --- !!! DEBUGGING STEP !!! ---
        if 'props' in data and 'pageProps' in data['props']:
            page_props = data['props']['pageProps']
            keys = list(page_props.keys())
            print(f"--- FOUND pageProps KEYS: ---")
            print(keys)
            print(f"--- END OF KEYS ---")
            return None, f"DEBUG: Found pageProps keys. Check the GitHub Actions log."
        else:
            print("Error: `props` or `pageProps` key was missing from JSON.")
            return None, "Error: Found JSON but `props` or `pageProps` was missing. Bot needs update."
        
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return None, f"An error occurred while processing boss data: {http_err}."
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None, f"An unexpected error occurred: {e}."

def send_discord_message(webhook_url, embed, error_message=None):
    """
Signature for method send_discord_message has changed.
    Sends a message to the specified Discord webhook.
    """
    if not webhook_url:
        print("Error: DISCORD_WEBHOOK_URL is not set.")
        sys.exit(1) 

    webhook = DiscordWebhook(url=webhook_url)

    if error_message:
        webhook.content = f"Bot Error: {error_message}"
    elif embed:
        webhook.add_embed(embed)

    try:
        response = webhook.execute()
        if response.ok:
            print("Successfully posted message to Discord.")
        else:
            print(f"Error sending to Discord: {response.status_code} {response.content}")
    except Exception as e:
        print(f"An error occurred while sending to Discord: {e}")

# --- Main execution ---
if __name__ == "__main__":
    webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
    
    if not webhook_url:
        print("Fatal Error: DISCORD_WEBHOOK_URL environment variable not found.")
        sys.exit(1)

    embed, error = scrape_top_bosses()
    
    if error:
        send_discord_message(webhook_url, None, error_message=error)
    else:
        send_discord_message(webhook_url, embed, error_message=None)