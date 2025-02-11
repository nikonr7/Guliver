from colorama import init, Fore, Style
import sys
import time

init()

def print_step(message):
    """Print a step with formatting."""
    print(f"\n{Fore.BLUE}➜ {message}{Style.RESET_ALL}")

def print_success(message):
    """Print a success message with formatting."""
    print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")

def print_error(message):
    """Print an error message with formatting."""
    print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}")

def loading_spinner(message):
    """Display a loading spinner with a message."""
    spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    i = 0
    while True:
        sys.stdout.write(f'\r{Fore.YELLOW}{spinner[i]}{Style.RESET_ALL} {message}')
        sys.stdout.flush()
        time.sleep(0.1)
        i = (i + 1) % len(spinner)

def print_banner():
    """Print a welcome banner for the application."""
    banner = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════╗
║                Reddit Market Research Tool                  ║
║           Search, Analyze, and Extract Insights            ║
╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""