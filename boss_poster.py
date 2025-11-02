# Description:
# This script scrapes the Exevo Pan boss tracker and posts the top 5
# bosses to a Discord channel using a Webhook.
# It's designed to be run by a scheduler like GitHub Actions.

import requests
from bs4 import BeautifulSoup
from discord_webhook import DiscordWebhook, DiscordEmbed
import os
import sys

# This is the main boss page.
BOSS_TRACKER_URL = "https://www.exevopan.com/bosses"

def scrape_top_bosses():
    """
    Scrapes the Exevo Pan boss tracker to find the top 5 bosses
    by spawn chance. Returns a formatted Discord embed.
    """
    print(f"Attempting to scrape boss data from: {BOSS_TRACKER_URL}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
    }

    try:
        session = requests.Session()
        response = session.get(BOSS_TRACKER_URL, headers=headers)
        response.raise_for_status()

        # --- !!! DEBUGGING STEP !!! ---
        # We are printing the start of the HTML to see its structure.
        html_content = response.text
        print("--- START OF HTML ---")
        print(html_content[:2000]) # Print the first 2000 chars
        print("--- END OF HTML ---")
        
        # We will intentionally stop here for debugging.
        return None, "DEBUG: Printed HTML snippet to log. Check GitHub Actions."
        
        # --- The old logic (which failed) is below ---
        
        soup = BeautifulSoup(response.text, 'html.parser')
        bosses_data = []
        boss_articles = soup.find_all('article')
        
        if not boss_articles:
            print("Error: Could not find any boss <article> elements. The HTML structure might have changed.")
            return None, "Error: Could not find boss data on Exevo Pan. The website's HTML structure may have changed."

        # ... (rest of the parsing logic) ...

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return None, f"An error occurred while processing boss data: {http_err}. The site may be blocking the bot."
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None, f"An unexpected error occurred: {e}."

def send_discord_message(webhook_url, embed, error_message=None):
    """
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