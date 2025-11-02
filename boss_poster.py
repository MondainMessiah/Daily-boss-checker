# Description:
# This script scrapes the Tibia boss tracker and posts the top 5
# bosses to a Discord channel using a Webhook.
# It's designed to be run by a scheduler like GitHub Actions.

import requests
from bs4 import BeautifulSoup
from discord_webhook import DiscordWebhook, DiscordEmbed
import re
import os
import sys

# The URL for the "Celesta" boss tracker.
BOSS_TRACKER_URL = "https://www.tibia-statistic.com/bosshunter/details/celesta"

def scrape_top_bosses():
    """
    Scrapes the boss tracker website to find the top 5 bosses
    by spawn chance. Returns a formatted message string.
    """
    print("Attempting to scrape boss data...")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(BOSS_TRACKER_URL, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        bosses_data = []

        # --- IMPORTANT ---
        # This selector targets rows in a table with the class "table-striped".
        # If the site layout changes, this is the line you'll need to update.
        # Right-click the table on the site and "Inspect" to find the new selectors.
        boss_rows = soup.select('table.table-striped > tbody > tr')
        
        if not boss_rows:
            print("Error: Could not find any boss rows. The HTML structure might have changed.")
            return None, "Error: Could not find boss data. The website's HTML structure may have changed."

        chance_regex = re.compile(r'\((\d+)%\)')

        for row in boss_rows:
            cells = row.find_all('td')
            # Assumes: Cell 0 has name, Cell 4 has chance.
            # This is a guess. Verify by inspecting the site.
            if len(cells) > 4:
                boss_name_element = cells[0].find('a')
                chance_text = cells[4].text
                
                if boss_name_element:
                    boss_name = boss_name_element.text.strip()
                    match = chance_regex.search(chance_text)
                    if match:
                        chance_percent = int(match.group(1))
                        bosses_data.append((boss_name, chance_percent))

        if not bosses_data:
            print("Error: Found boss rows, but couldn't parse name/chance.")
            return None, "Error: Found boss data but couldn't parse it. Bot needs updating."

        # Sort bosses by chance (highest first) and take top 5
        bosses_data.sort(key=lambda x: x[1], reverse=True)
        top_5_bosses = bosses_data[:5]

        # --- Create the Discord Embed ---
        embed = DiscordEmbed(title='📅 Daily Boss Hunter Report (Celesta)', color='03b2f8')
        embed.set_description("Here are the top 5 bosses with the highest spawn chance today:")

        description_text = ""
        for i, (name, chance) in enumerate(top_5_bosses, 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "•"
            description_text += f"{emoji} **{name}**: {chance}%\n"
        
        embed.add_embed_field(name='Top 5 Chances', value=description_text)
        embed.set_footer(text='Data from tibia-statistic.com')
        embed.set_timestamp()

        print("Successfully scraped and formatted boss data.")
        return embed, None

    except Exception as e:
        print(f"An error occurred during scraping: {e}")
        return None, f"An error occurred while processing boss data: {e}."

def send_discord_message(webhook_url, embed, error_message=None):
    """
    Sends a message to the specified Discord webhook.
    """
    if not webhook_url:
        print("Error: DISCORD_WEBHOOK_URL is not set.")
        sys.exit(1) # Exit with an error code

    webhook = DiscordWebhook(url=webhook_url)

    if error_message:
        # Send a plain text error
        webhook.content = f"Bot Error: {error_message}"
    elif embed:
        # Add the embed to the webhook
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
    # Get the Webhook URL from the GitHub Actions "Secrets"
    webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
    
    if not webhook_url:
        print("Fatal Error: DISCORD_WEBHOOK_URL environment variable not found.")
        sys.exit(1)

    embed, error = scrape_top_bosses()
    
    if error:
        send_discord_message(webhook_url, None, error_message=error)
    else:
        send_discord_message(webhook_url, embed, error_message=None)
