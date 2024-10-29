import logging
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from telegram import Update, ForceReply
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# To keep track of user states
user_states = {}

# Function to find Instagram username from ID
def find_username(user_id: str) -> str:
    service = FirefoxService(GeckoDriverManager().install())
    options = Options()
    options.headless = True
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Firefox(service=service, options=options)
    
    try:
        driver.get('https://commentpicker.com/instagram-username.php')

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, 'instagram-userid')))

        id_input = driver.find_element(By.ID, 'instagram-userid')
        id_input.send_keys(user_id)

        x_value = driver.find_element(By.ID, 'captcha-x').text
        y_value = driver.find_element(By.ID, 'captcha-y').text
        total_sum = int(x_value) + int(y_value)

        sum_input = driver.find_element(By.ID, 'captcha')
        sum_input.send_keys(str(total_sum))

        submit_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'get-username-button')))
        driver.execute_script("arguments[0].click();", submit_button)

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.generator-results__results-link')))
        
        result_link = driver.find_element(By.CSS_SELECTOR, '.generator-results__results-link')
        username = result_link.text
        return username
    except Exception as e:
        logger.error(f"Error retrieving username: {e}")
        return "Could not retrieve the username."
    finally:
        driver.quit()

# Function to find Instagram ID from username
def find_instagram_id(username: str) -> str:
    service = FirefoxService(GeckoDriverManager().install())
    options = Options()
    options.headless = True
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Firefox(service=service, options=options)
    
    try:
        driver.get(f'https://www.instagram.com/{username}/')

        # Wait for the page to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

        # Get the entire page source
        page_source = driver.page_source
        
        # Use regex to find the profile_id anywhere in the page source
        match = re.search(r'"profile_id":"(\d+)"', page_source)
        if match:
            profile_id = match.group(1)
            return profile_id
        else:
            return "Profile ID not found."
    except Exception as e:
        logger.error(f"Error retrieving profile ID: {e}")
        return "Could not retrieve the profile ID."
    finally:
        driver.quit()

# Command handler functions
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    user_states[user.id] = 'menu'  # Set the initial state to menu
    await update.message.reply_html(
        rf"Hello {user.mention_html()}! Use the menu below:"
        "\n1. Find Instagram Username from ID\n"
        "\n2. Find Instagram ID by Username\n"
        "\n3. Exit\n",
        reply_markup=ForceReply(selective=True),
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the user's message."""
    user = update.effective_user
    user_message = update.message.text.strip()

    if user_states.get(user.id) == 'menu':
        if user_message == "1":  # Find username by ID
            user_states[user.id] = 'waiting_for_id'  # Change state to waiting for ID
            await update.message.reply_text("Please enter the Instagram user ID:")
        elif user_message == "2":  # Find ID by username
            user_states[user.id] = 'waiting_for_username'  # Change state to waiting for username
            await update.message.reply_text("Please enter the Instagram username:")
        elif user_message == "3":  # User wants to exit
            await update.message.reply_text("Goodbye!")
            user_states[user.id] = 'exit'  # Change state to exit
        else:
            await update.message.reply_text("Invalid option. Please choose:\n1. Find Instagram Username from ID\n2. Find Instagram ID by Username\n3. Exit")
    elif user_states.get(user.id) == 'waiting_for_id':  # User is waiting for ID input
        await update.message.reply_text("Processing...")  # Immediate response
        username = find_username(user_message)
        await update.message.reply_text(f"Retrieved username: {username}")
        user_states[user.id] = 'menu'  # Reset state back to menu
    elif user_states.get(user.id) == 'waiting_for_username':  # User is waiting for username input
        await update.message.reply_text("Processing...")  # Immediate response
        profile_id = find_instagram_id(user_message)
        await update.message.reply_text(f"Retrieved profile ID: {profile_id}")
        user_states[user.id] = 'menu'  # Reset state back to menu

def main() -> None:
    """Start the bot."""
    application = ApplicationBuilder().token("7845194572:AAG3mvAG91W7ForHGyKvwMjF0-ODXS5w8OQ").build()

    # Register command and message handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Start the Bot
    application.run_polling()

if __name__ == '__main__':
    main()
