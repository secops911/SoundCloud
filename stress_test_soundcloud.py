import threading
import time
import requests
import os
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from datetime import datetime

# Initialize Rich console for better CLI experience
console = Console()

# Track the number of completed sessions and errors
completed_sessions = 0
session_errors = 0
lock = threading.Lock()
LOG_FILE = "stress_test.log"

# Function to log messages
def log_message(message):
    """Logs a message to the log file."""
    with open(LOG_FILE, "a") as log:
        log.write(f"[{datetime.now()}] {message}\n")

# Function to play the song
def play_song(session_id, song_url, listen_duration, max_retries=3):
    """Simulates playing a song for the specified duration."""
    global completed_sessions, session_errors

    retries = 0
    while retries <= max_retries:
        try:
            with lock:
                console.print(f"[blue]Session {session_id} started.[/blue]")
                log_message(f"Session {session_id} started.")

            # Send a GET request to simulate playing the song
            response = requests.get(song_url, timeout=10)

            if response.status_code == 200:
                with lock:
                    console.print(f"[green]Session {session_id}: Successfully accessed the song.[/green]")
                    log_message(f"Session {session_id}: Successfully accessed the song.")
                break
            else:
                retries += 1
                with lock:
                    console.print(f"[red]Session {session_id}: Failed to access the song. Status code: {response.status_code}. Retrying ({retries}/{max_retries})...[/red]")
                    log_message(f"Session {session_id}: Failed to access the song. Status code: {response.status_code}. Retrying ({retries}/{max_retries})...")

        except requests.RequestException as e:
            retries += 1
            with lock:
                console.print(f"[red]Session {session_id}: Error occurred - {e}. Retrying ({retries}/{max_retries})...[/red]")
                log_message(f"Session {session_id}: Error occurred - {e}. Retrying ({retries}/{max_retries})...")

        time.sleep(2)  # Wait before retrying

    # If retries exceeded
    if retries > max_retries:
        with lock:
            session_errors += 1
            console.print(f"[red]Session {session_id}: Failed after {max_retries} retries.[/red]")
            log_message(f"Session {session_id}: Failed after {max_retries} retries.")

    # Simulate listening to the song for the specified duration
    time.sleep(listen_duration)

    # Mark the session as complete
    with lock:
        completed_sessions += 1
        console.print(f"[cyan]Session {session_id} completed.[/cyan]")
        log_message(f"Session {session_id} completed.")

def manage_sessions(song_url, total_sessions, concurrent_sessions, listen_duration):
    """Manages the concurrent sessions."""
    threads = []

    # Write initial log
    log_message(f"Starting stress test: {total_sessions} sessions, {concurrent_sessions} concurrent sessions, {listen_duration}s duration.")

    # Display progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task("[yellow]Running sessions...", total=total_sessions)

        for session_id in range(1, total_sessions + 1):
            # Wait if there are already concurrent_sessions active
            while threading.active_count() > concurrent_sessions:
                time.sleep(0.5)

            # Start a new session
            thread = threading.Thread(target=play_song, args=(session_id, song_url, listen_duration))
            thread.start()
            threads.append(thread)

            # Update progress bar
            progress.update(task, advance=1)

        # Wait for all threads to finish
        for thread in threads:
            thread.join()

    console.print("[bold green]All sessions completed![/bold green]")
    log_message(f"Stress test completed. Total errors: {session_errors}.")

def main():
    """CLI Interface for the SoundCloud stress test script."""
    # Clear the screen for a clean interface
    os.system('cls' if os.name == 'nt' else 'clear')

    console.print("[bold cyan]Welcome to the SoundCloud Stress Test Tool[/bold cyan]")

    # Ask the user for the song URL
    song_url = console.input("[bold green]Enter the SoundCloud song URL:[/bold green] ").strip()

    # Ask the user for the total number of sessions
    total_sessions = console.input("[bold green]Enter the total number of sessions:[/bold green] ").strip()
    total_sessions = int(total_sessions)

    # Ask the user for the number of concurrent sessions
    concurrent_sessions = console.input("[bold green]Enter the number of concurrent sessions:[/bold green] ").strip()
    concurrent_sessions = int(concurrent_sessions)

    # Ask the user for the listening duration
    listen_duration = console.input("[bold green]Enter the listening duration (in seconds):[/bold green] ").strip()
    listen_duration = int(listen_duration)

    # Confirm the parameters
    console.print(f"\n[bold magenta]Configuration:[/bold magenta]")
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("Parameter", style="dim")
    table.add_column("Value")
    table.add_row("Song URL", song_url)
    table.add_row("Total Sessions", str(total_sessions))
    table.add_row("Concurrent Sessions", str(concurrent_sessions))
    table.add_row("Listening Duration", f"{listen_duration} seconds")
    console.print(table)

    # Confirm to start
    user_input = console.input("[bold green]Ready to start the stress test? (y/n): [/bold green]").strip().lower()
    if user_input not in ['y', 'yes']:
        console.print("[bold red]Aborted by user.[/bold red]")
        return

    # Start the stress test
    manage_sessions(song_url, total_sessions, concurrent_sessions, listen_duration)

if __name__ == "__main__":
    main()

