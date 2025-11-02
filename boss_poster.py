# Description:
# FINAL SCRIPT (v3 - Test)
# This script scrapes the generic /bosses page to see if
# the default server's data is scrape-able. This is to confirm
# the site is blocking our server-specific request.

import requests
import json
from bs4 import BeautifulSoup
from discord_webhook import DiscordWebhook, DiscordEmbed
import os
import sys

# Back to the generic URL for testing
BOSS_TRACKER_URL = "https://www.exevopan.com/bosses"

def scrape_top_bosses():
    """
    Scrapes the Exevo Pan boss tracker by parsing its __NEXT_DATA__ JSON.
    Returns a formatted Discord embed or an error message.
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
            print("Error: Could not find __NEXT_DATA__ script tag.")
            return None, "Error: Could not find the `__NEXT_DATA__` script tag on Exevo Pan. The bot needs to be updated."

        data = json.loads(next_data_script.string)
        page_props = data.get('props', {}).get('pageProps', {})
        boss_list = page_props.get('bossChances', [])
        
        # 'server' key might not exist here, so we'll add a default
        server_name = page_props.get('server', 'Default Server')
        
        if not boss_list:
            print("Error: Found __NEXT_DATA__ but 'bossChances' key was missing or empty.")
            return None, "Error: Found the data blob but the 'bossChances' list was missing. The bot needs to be updated."

        bosses_data = []
        for boss in boss_list:
            if 'name' in boss and 'chance' in boss and boss['chance'] > 0:
                bosses_data.append((boss['name'], boss['chance']))
        
        # --- Create the Discord Embed ---
        embed = DiscordEmbed(title=f'📅 Daily Boss Report ({server_name})', color='00e676')
        embed.set_url(BOSS_TRACKER_URL)
        embed.set_footer(text='Data from ExevoPan.com')
        embed.set_timestamp()

        if not bosses_data:
            print("No bosses with a chance > 0 found.")
            embed.set_color('607d8b') # Grey color
            embed.add_embed_field(
                name='No Bosses Today', 
                value='No bosses with a spawn chance > 0% were found.'
            )
        else:
            print(f"Found {len(bosses_data)} bosses. Sorting for top 5.")
            bosses_data.sort(key=lambda x: x[1], reverse=True)
            top_5_bosses = bosses_data[:5]
            
            description_text = ""
            for i, (name, chance) in enumerate(top_5_bosses, 1):
                emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "•"
                description_text += f"{emoji} **{name}**: {chance:.0f}%\n"
            
            embed.add_embed_field(name='Top 5 Chances', value=description_text)

        print(f"Successfully scraped and formatted boss data for {server_name}.")
        return embed, None

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return None, f"An error occurred while processing boss data: {http_err}."
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