import os
import sys
import time
import random
import subprocess
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from datetime import datetime

# Logging function
LOG_FILE = "playback_test.log"

def log_message(message):
    """Logs a message to the log file."""
    with open(LOG_FILE, "a") as log:
        log.write(f"[{datetime.now()}] {message}\n")

# Dependency checker and installer
def check_and_install_dependencies():
    """Checks and installs required dependencies."""
    required_packages = ["selenium", "requests"]
    missing_packages = [pkg for pkg in required_packages if not is_package_installed(pkg)]

    # Install missing Python packages
    if missing_packages:
        print(f"Installing missing Python packages: {', '.join(missing_packages)}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_packages])

    # Ensure ChromeDriver is installed
    if not os.path.exists("/usr/bin/chromedriver"):
        print("Installing ChromeDriver...")
        subprocess.check_call(["sudo", "apt", "install", "-y", "chromium-chromedriver"])

def is_package_installed(package_name):
    """Checks if a Python package is installed."""
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False

# Tor IP Checker
def get_tor_ip():
    """Fetches the current public IP from Tor."""
    try:
        proxies = {
            "http": "socks5h://127.0.0.1:9050",
            "https": "socks5h://127.0.0.1:9050",
        }
        response = requests.get("https://api.ipify.org?format=json", proxies=proxies, timeout=10)
        response.raise_for_status()
        return response.json().get("ip", "Unknown IP")
    except Exception as e:
        log_message(f"Error fetching Tor IP: {e}")
        return "Unknown IP"

# Path to the ChromeDriver executable
CHROME_DRIVER_PATH = "/usr/bin/chromedriver"

def play_song_with_selenium(song_url, listen_duration, session_id, retries=3):
    """Simulates playing a song on SoundCloud with Selenium over Tor."""
    options = Options()
    options.add_argument('--headless')  # Run in headless mode
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    # Add a user-agent for realism
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )

    # Route Selenium traffic through Tor's SOCKS5 proxy
    options.add_argument('--proxy-server=socks5://127.0.0.1:9050')

    service = Service(CHROME_DRIVER_PATH)

    for attempt in range(1, retries + 1):
        try:
            # Start the WebDriver
            driver = webdriver.Chrome(service=service, options=options)

            # Log the current Tor IP
            tor_ip = get_tor_ip()
            log_message(f"Session {session_id}: Using Tor IP {tor_ip}")

            # Open the SoundCloud song page
            log_message(f"Session {session_id}: Accessing {song_url}...")
            driver.get(song_url)

            # Allow page to load
            time.sleep(5)

            # Find the play button and click it
            log_message(f"Session {session_id}: Attempting to play the song...")
            play_button = driver.find_element(By.CLASS_NAME, "playControl")
            if "playing" not in play_button.get_attribute("class"):
                play_button.click()

            # Simulate listening duration
            log_message(f"Session {session_id}: Playing for {listen_duration} seconds...")
            time.sleep(listen_duration)

            # Confirm playback completed
            log_message(f"Session {session_id}: Playback complete.")
            return  # Exit the function if successful

        except Exception as e:
            log_message(f"Session {session_id}, Attempt {attempt}: Error occurred - {e}")

        finally:
            try:
                driver.quit()
            except Exception:
                pass

    # If all retries fail
    log_message(f"Session {session_id}: Failed after {retries} attempts.")

def main():
    """Main function to run multiple playback sessions."""
    # Check and install dependencies
    check_and_install_dependencies()

    # Ask for user input
    song_url = input("Enter the SoundCloud song URL: ").strip()
    total_sessions = int(input("Enter the total number of sessions: ").strip())
    listen_duration = int(input("Enter the listening duration (in seconds): ").strip())

    # Initialize session tracking
    completed_sessions = 0
    failed_sessions = 0

    for session_id in range(1, total_sessions + 1):
        try:
            # Play the song with Selenium
            play_song_with_selenium(song_url, listen_duration, session_id)
            completed_sessions += 1
        except Exception as e:
            failed_sessions += 1
            log_message(f"Session {session_id}: Failed - {e}")

        # Wait a bit between sessions to allow Tor to rotate IPs
        time.sleep(30)  # Matches Tor's IP rotation interval

    # Final summary
    log_message(f"Stress test completed: {completed_sessions} successful, {failed_sessions} failed.")
    print(f"\nStress test completed: {completed_sessions} successful, {failed_sessions} failed.")
    print(f"Check the log file ({LOG_FILE}) for details.")

if __name__ == "__main__":
    main()

