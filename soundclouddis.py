import os
import sys
import time
import subprocess
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

LOG_FILE = "playback_test.log"
console = Console()

BANNER = """
[bold green]
███████╗ ██████╗ ██╗   ██╗███╗   ██╗ ██████╗ ██████╗ ██╗     ██████╗ 
██╔════╝██╔═══██╗██║   ██║████╗  ██║██╔════╝██╔═══██╗██║     ██╔══██╗
███████╗██║   ██║██║   ██║██╔██╗ ██║██║     ██║   ██║██║     ██║  ██║
╚════██║██║▄▄ ██║██║   ██║██║╚██╗██║██║     ██║   ██║██║     ██║  ██║
███████║╚██████╔╝╚██████╔╝██║ ╚████║╚██████╗╚██████╔╝███████╗██████╔╝
╚══════╝ ╚══▀▀═╝  ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝ ╚═════╝ ╚══════╝╚═════╝ 
[/bold green]
"""

def log_message(message):
    """Logs a message to the log file."""
    with open(LOG_FILE, "a") as log:
        log.write(f"[{datetime.now()}] {message}\n")
    console.log(message)

def check_and_install_dependencies():
    """Checks and installs required dependencies."""
    required_packages = ["selenium", "requests", "rich"]
    missing_packages = [pkg for pkg in required_packages if not is_package_installed(pkg)]

    if missing_packages:
        console.print(f"[yellow]Installing missing Python packages: {', '.join(missing_packages)}...[/yellow]")
        log_message(f"Installing missing Python packages: {', '.join(missing_packages)}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing_packages])

    if not os.path.exists("/usr/bin/chromedriver"):
        console.print("[yellow]Installing ChromeDriver...[/yellow]")
        log_message("Installing ChromeDriver...")
        subprocess.check_call(["sudo", "apt", "install", "-y", "chromium-chromedriver"])

    try:
        subprocess.check_call(["sudo", "apt", "install", "-y", "xdg-utils"])
    except Exception as e:
        log_message(f"Error installing xdg-utils: {e}")

def is_package_installed(package_name):
    """Checks if a Python package is installed."""
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False

def check_tor_status():
    """Checks if the Tor service is running."""
    try:
        result = subprocess.run(["systemctl", "is-active", "tor"], capture_output=True, text=True)
        if result.stdout.strip() != "active":
            console.print("[red bold]Error: Tor service is not running.[/red bold]")
            log_message("[ERROR] Tor service is not running.")
            sys.exit(1)
    except Exception as e:
        log_message(f"Error checking Tor status: {e}")
        sys.exit(1)

def get_tor_ip(retries=3):
    """Fetches the current public IP from Tor."""
    for attempt in range(1, retries + 1):
        try:
            proxies = {"http": "socks5h://127.0.0.1:9050", "https": "socks5h://127.0.0.1:9050"}
            response = requests.get("https://api.ipify.org?format=json", proxies=proxies, timeout=10)
            response.raise_for_status()
            return response.json().get("ip", "Unknown IP")
        except Exception as e:
            log_message(f"Attempt {attempt}: Error fetching Tor IP - {e}")
            time.sleep(5)
    log_message("Failed to fetch Tor IP after multiple attempts.")
    return "Unknown IP"

def play_song_with_selenium(song_url, listen_duration, session_id):
    """Simulates playing a song on SoundCloud with Selenium over Tor."""
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--proxy-server=socks5://127.0.0.1:9050')
    options.add_argument('--disable-features=NetworkService,NetworkServiceInProcess')
    options.add_argument('--disable-background-timer-throttling')
    options.add_argument('--disable-backgrounding-occluded-windows')
    options.add_argument('--disable-renderer-backgrounding')

    service = Service("/usr/bin/chromedriver")

    try:
        log_message(f"Session {session_id}: Initializing WebDriver...")
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(60)
        log_message(f"Session {session_id}: WebDriver initialized successfully.")

        tor_ip = get_tor_ip()
        log_message(f"Session {session_id}: Using Tor IP {tor_ip}")
        log_message(f"Session {session_id}: Accessing {song_url}...")
        driver.get(song_url)

        log_message(f"Session {session_id}: Waiting for the play button...")
        play_button = WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.CLASS_NAME, "playControl"))
        )
        log_message(f"Session {session_id}: Play button found. Attempting to click...")
        if "playing" not in play_button.get_attribute("class"):
            play_button.click()

        log_message(f"Session {session_id}: Playing for {listen_duration} seconds...")
        time.sleep(listen_duration)

        log_message(f"Session {session_id}: Playback complete.")
    except Exception as e:
        log_message(f"Session {session_id}: Error - {e}")
    finally:
        try:
            driver.quit()
        except Exception:
            pass

def run_in_background(script_path):
    """Runs the script in the background using nohup."""
    console.print("[cyan bold]Running in the background...[/cyan bold]")
    command = f"nohup python3 {script_path} > playback_output.log 2>&1 &"
    os.system(command)
    console.print("[bold green]Script is now running in the background. Check playback_output.log for progress.[/bold green]")
    sys.exit(0)

def main():
    """Main function."""
    os.environ["XDG_RUNTIME_DIR"] = "/tmp/runtime-root"
    os.makedirs(os.environ["XDG_RUNTIME_DIR"], exist_ok=True)
    os.chmod(os.environ["XDG_RUNTIME_DIR"], 0o700)

    check_and_install_dependencies()
    check_tor_status()

    console.print(BANNER)
    console.print("[bold cyan]Welcome to the SoundCloud Playback Stress Tester![/bold cyan]\n")
    song_url = Prompt.ask("[green bold]Enter the SoundCloud song URL[/green bold]")
    total_sessions = int(Prompt.ask("[green bold]Enter the total number of sessions[/green bold]", default="10"))
    listen_duration = int(Prompt.ask("[green bold]Enter the listening duration (in seconds)[/green bold]", default="60"))

    # Ask if the script should run in the background
    run_background = Prompt.ask("[green bold]Do you want to run the script in the background? (yes/no)[/green bold]", default="no")
    if run_background.lower() == "yes":
        run_in_background(sys.argv[0])

    console.print("\n[bold magenta]Configuration[/bold magenta]:")
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("Parameter", style="dim")
    table.add_column("Value")
    table.add_row("Song URL", song_url)
    table.add_row("Total Sessions", str(total_sessions))
    table.add_row("Listening Duration", f"{listen_duration} seconds")
    console.print(table)

    completed_sessions = 0
    failed_sessions = 0

    for session_id in range(1, total_sessions + 1):
        console.print(f"\n[cyan bold]Starting session {session_id}/{total_sessions}...[/cyan bold]")
        try:
            play_song_with_selenium(song_url, listen_duration, session_id)
            completed_sessions += 1
        except Exception as e:
            failed_sessions += 1
            log_message(f"Session {session_id}: Failed - {e}")
        time.sleep(30)

    console.print(f"\n[bold green]Stress test completed: {completed_sessions} successful, {failed_sessions} failed.[/bold green]")
    log_message(f"Stress test completed: {completed_sessions} successful, {failed_sessions} failed.")

if __name__ == "__main__":
    main()

