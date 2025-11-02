# Description:
# This script scrapes the Exevo Pan boss tracker for "Celesta"
# and posts the top 5 bosses to a Discord channel using a Webhook.
# It's designed to be run by a scheduler like GitHub Actions.

import requests
from bs4 import BeautifulSoup
from discord_webhook import DiscordWebhook, DiscordEmbed
import os
import sys

# --- THIS IS THE CORRECTED URL ---
BOSS_TRACKER_URL = "https://www.exevopan.com/bosses/celesta"

def scrape_top_bosses():
    """
    Scrapes the Exevo Pan boss tracker to find the top 5 bosses
    by spawn chance. Returns a formatted Discord embed.
    """
    print(f"Attempting to scrape boss data from: {BOSS_TRACKER_URL}")
    
    # These headers make our request look like it's from a real browser
    # to avoid a "403 Forbidden" error.
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
    }

    try:
        session = requests.Session()
        response = session.get(BOSS_TRACKER_URL, headers=headers)
        
        # Check if the request was successful
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        bosses_data = []

        # --- IMPORTANT (NEW EXEVO PAN LOGIC) ---
        # This is a guess at the Exevo Pan HTML structure.
        # It assumes each boss is in an <article> tag.
        # It looks for a <strong> tag with a '%' and an <a> tag
        # (which holds the name) inside each article.
        
        boss_articles = soup.find_all('article')
        
        if not boss_articles:
            print("Error: Could not find any boss <article> elements. The HTML structure might have changed.")
            return None, "Error: Could not find boss data on Exevo Pan. The website's HTML structure may have changed."

        for item in boss_articles:
            # Find the boss name, which is usually a link
            boss_name_element = item.find('a')
            # Find the chance, which is usually in a <strong> tag
            chance_element = item.find('strong')

            if boss_name_element and chance_element:
                boss_name = boss_name_element.text.strip()
                chance_text = chance_element.text.strip()
                
                # Check if the text is a percentage
                if chance_text.endswith('%'):
                    try:
                        # Remove '%' and convert to float, then int
                        chance_percent = int(float(chance_text.replace('%', '')))
                        bosses_data.append((boss_name, chance_percent))
                    except ValueError:
                        # This skips any 'strong' tags that aren't percentages
                        continue

        if not bosses_data:
            print("Error: Found boss articles, but couldn't parse name/chance.")
            return None, "Error: Found boss articles but couldn't parse name/chance. Bot needs updating."

        # Sort bosses by chance (highest first) and take top 5
        bosses_data.sort(key=lambda x: x[1], reverse=True)
        top_5_bosses = bosses_data[:5]
        
        if not top_5_bosses:
             print("Error: Parsed bosses but top 5 list is empty.")
             return None, "Error: Parsed bosses but top 5 list is empty."

        # --- Create the Discord Embed ---
        embed = DiscordEmbed(title='📅 Daily Boss Hunter Report (Celesta)', color='00e676') # Green color
        embed.set_url(BOSS_TRACKER_URL)
        embed.set_description("Here are the top 5 bosses with the highest spawn chance today:")

        description_text = ""
        for i, (name, chance) in enumerate(top_5_bosses, 1):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "•"
            description_text += f"{emoji} **{name}**: {chance}%\n"
        
        embed.add_embed_field(name='Top 5 Chances', value=description_text)
        embed.set_footer(text='Data from ExevoPan.com')
        embed.set_timestamp()

        print("Successfully scraped and formatted boss data from Exevo Pan.")
        return embed, None

    except requests.exceptions.HTTPError as http_err:
        # Specifically catch HTTP errors (like 403)
        print(f"HTTP error occurred: {http_err}")
        return None, f"An error occurred while processing boss data: {http_err}. The site may be blocking the bot."
    except Exception as e:
        # Catch all other errors
        print(f"An unexpected error occurred: {e}")
        return None, f"An unexpected error occurred: {e}."

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