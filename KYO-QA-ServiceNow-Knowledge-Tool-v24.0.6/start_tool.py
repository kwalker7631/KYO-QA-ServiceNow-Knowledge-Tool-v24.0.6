# KYO QA ServiceNow - Smart Python Launcher with Efficient Setup
from version import VERSION
import argparse

import sys
import subprocess
import shutil
import time
import threading
from pathlib import Path
from logging_utils import setup_logger, log_info, log_error, log_warning

logger = setup_logger("startup")

LOGS_DIR = Path(__file__).parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Colors for console output (Windows and ANSI)
try:
    from colorama import init, Fore, Style
    init()  # Initialize colorama
    COLOR_INFO = Fore.CYAN
    COLOR_SUCCESS = Fore.GREEN
    COLOR_WARNING = Fore.YELLOW
    COLOR_ERROR = Fore.RED
    COLOR_RESET = Style.RESET_ALL
except ImportError:
    # Fallback if colorama not installed
    COLOR_INFO = ""
    COLOR_SUCCESS = ""
    COLOR_WARNING = ""
    COLOR_ERROR = ""
    COLOR_RESET = ""

# Spinner animation for console
class ConsoleSpinner:
    def __init__(self):
        self.spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.running = False
        self.index = 0
        self.thread = None
        
    def start(self, message="Working..."):
        self.message = message
        self.running = True
        self.thread = threading.Thread(target=self._spin)
        self.thread.daemon = True
        self.thread.start()
        
    def _spin(self):
        while self.running:
            char = self.spinner_chars[self.index]
            sys.stdout.write(f"\r{char} {self.message}")
            sys.stdout.flush()
            self.index = (self.index + 1) % len(self.spinner_chars)
            time.sleep(0.1)
            
    def stop(self, final_message=None):
        self.running = False
        if self.thread:
            self.thread.join(timeout=0.2)
        if final_message:
            sys.stdout.write(f"\r✓ {final_message}\n")
        else:
            sys.stdout.write("\r" + " " * (len(self.message) + 2) + "\r")
        sys.stdout.flush()

# Visual progress functions
def print_header():
    """Print a styled header."""
    header_width = 70
    print("\n" + "=" * header_width)
    title = f"KYO QA ServiceNow Tool Smart Setup {VERSION}"
    padding = (header_width - len(title)) // 2
    print(" " * padding + COLOR_INFO + title + COLOR_RESET)
    print("=" * header_width + "\n")

def print_step(step_number, total_steps, message):
    """Print a step in the setup process."""
    print(f"[{step_number}/{total_steps}] {COLOR_INFO}{message}{COLOR_RESET}")

def print_success(message):
    """Print a success message."""
    print(f"    {COLOR_SUCCESS}✓ {message}{COLOR_RESET}")

def print_warning(message):
    """Print a warning message."""
    print(f"    {COLOR_WARNING}⚠ {message}{COLOR_RESET}")

def print_error(message):
    """Print an error message."""
    print(f"    {COLOR_ERROR}✗ {message}{COLOR_RESET}")

def print_info(message):
    """Print an info message."""
    print(f"    {COLOR_INFO}ℹ {message}{COLOR_RESET}")


def parse_arguments(args=None):
    """Parse command line options."""
    parser = argparse.ArgumentParser(
        description="KYO QA ServiceNow Tool Launcher"
    )
    parser.add_argument(
        "--repair",
        action="store_true",
        help="Rebuild the virtual environment and reinstall dependencies",
    )
    return parser.parse_args(args)

def check_python_version():
    """Check if Python version is 3.11 or higher."""
    print_step(1, 4, "Checking Python environment...")
    spinner = ConsoleSpinner()
    spinner.start("Verifying Python version...")
    
    time.sleep(0.5)  # Give a moment to see the spinner
    
    if sys.version_info < (3, 11):
        spinner.stop()
        print_error(f"Python 3.11+ is required. Current: {sys.version}")
        log_error(logger, f"Python 3.11+ is required. Current: {sys.version}")
        sys.exit(1)
    
    spinner.stop(f"Python version {sys.version.split()[0]} is compatible.")
    log_info(logger, f"Python version is {sys.version}")
    print_success(f"Using Python {sys.version.split()[0]}")

def check_existing_virtualenv():
    """Check if virtual environment already exists and is valid."""
    print_step(2, 4, "Checking virtual environment...")
    venv_dir = Path(__file__).parent / "venv"
    
    if not venv_dir.exists():
        print_info("Virtual environment not found - will create new one")
        log_info(logger, "No existing virtual environment found")
        return False
    
    # Check if Python executable exists in venv
    venv_python = venv_dir / "Scripts" / "python.exe"
    if not venv_python.exists():
        venv_python = venv_dir / "bin" / "python3"  # Linux/Mac
    
    if not venv_python.exists():
        print_warning("Virtual environment is incomplete - will recreate")
        log_warning(logger, "Virtual environment Python executable not found")
        return False
    
    # Test if the venv Python actually works
    spinner = ConsoleSpinner()
    spinner.start("Testing virtual environment...")
    
    try:
        result = subprocess.run(
            [str(venv_python), "-c", "import sys; print(sys.version)"],
            capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0:
            spinner.stop("Virtual environment is valid")
            print_success("Existing virtual environment is working")
            log_info(logger, "Virtual environment validation successful")
            return True
        else:
            spinner.stop()
            print_warning("Virtual environment test failed - will recreate")
            log_warning(
                logger,
                f"Virtual environment test failed: {result.stderr}"
            )
            return False
            
    except Exception as e:
        spinner.stop()
        print_warning("Virtual environment validation error - will recreate")
        log_warning(logger, f"Virtual environment validation error: {e}")
        return False

def create_virtualenv():
    """Create a virtual environment for the application."""
    venv_dir = Path(__file__).parent / "venv"
    
    spinner = ConsoleSpinner()
    
    # Remove existing if corrupted
    if venv_dir.exists():
        spinner.start("Removing corrupted virtual environment...")
        try:
            time.sleep(0.5)  # Pause for visual effect
            shutil.rmtree(venv_dir)
            spinner.stop("Old virtual environment removed")
            log_info(logger, "Corrupted virtual environment removed")
        except Exception as e:
            spinner.stop()
            print_error(f"Failed to remove existing environment: {e}")
            log_error(logger, f"Failed to remove virtual environment: {e}")
            sys.exit(1)
    
    spinner.start("Creating new virtual environment...")
    try:
        time.sleep(0.5)  # Pause for visual effect
        subprocess.check_call([sys.executable, "-m", "venv", "venv"], 
                            stdout=subprocess.DEVNULL, 
                            stderr=subprocess.DEVNULL)
        spinner.stop("Virtual environment created successfully")
        log_info(logger, "Virtual environment created")
        print_success("Virtual environment ready")
        return True
    except Exception as e:
        spinner.stop()
        print_error(f"Failed to create virtual environment: {e}")
        log_error(logger, f"Failed to create virtual environment: {e}")
        sys.exit(1)

def check_and_install_requirements():
    """Check existing packages and only install missing ones."""
    print_step(3, 4, "Checking and installing packages...")
    
    # Locate the Python executable in the virtual environment
    venv_python = Path(__file__).parent / "venv" / "Scripts" / "python.exe"
    if not venv_python.exists():
        venv_python = Path(__file__).parent / "venv" / "bin" / "python3"
        
    if not venv_python.exists():
        print_error("Could not locate virtual environment Python executable!")
        log_error(logger, "Could not locate venv python executable!")
        sys.exit(1)
    
    req_file = Path(__file__).parent / "requirements.txt"
    
    # Check if requirements are already satisfied
    spinner = ConsoleSpinner()
    spinner.start("Checking existing packages...")
    
    try:
        
        # Test critical packages
        critical_packages = ['pandas', 'PyMuPDF', 'openpyxl']
        missing_packages = []
        
        for package in critical_packages:
            try:
                result = subprocess.run(
                    [str(venv_python), "-c", f"import {package}"],
                    capture_output=True, timeout=5
                )
                if result.returncode != 0:
                    missing_packages.append(package)
            except:
                missing_packages.append(package)
        
        if not missing_packages:
            spinner.stop("All critical packages are already installed")
            print_success(
                "Dependencies are up to date - skipping installation"
            )
            log_info(logger, "All required packages already installed")
            return
        else:
            spinner.stop()
            print_info(f"Missing packages: {', '.join(missing_packages)}")
            log_info(logger, f"Missing packages detected: {missing_packages}")
            
    except Exception as e:
        spinner.stop()
        print_warning(f"Package check failed: {e}")
        log_warning(logger, f"Package check failed: {e}")
    
    # Upgrade pip first
    spinner = ConsoleSpinner()
    spinner.start("Upgrading pip...")
    
    try:
        subprocess.check_call(
            [str(venv_python), "-m", "pip", "install", "--upgrade", "pip"],
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )
        spinner.stop("Pip upgraded successfully")
    except Exception as e:
        spinner.stop()
        print_warning(f"Failed to upgrade pip: {e}")
        log_warning(logger, f"Failed to upgrade pip: {e}")
        # Continue anyway, this is not critical
    
    # Install requirements with progress tracking
    try:
        print_info("Installing missing packages...")
        
        # Install all requirements at once for efficiency
        spinner.start("Installing packages (this may take a few minutes)...")
        
        install_process = subprocess.run(
            [str(venv_python), "-m", "pip", "install", "-r", str(req_file)],
            capture_output=True, text=True
        )
        
        if install_process.returncode == 0:
            spinner.stop("Package installation completed")
            print_success("All packages installed successfully")
            log_info(logger, "Requirements installation completed")
        else:
            spinner.stop()
            print_warning("Some packages may have failed to install")
            log_warning(
                logger,
                f"Package installation warnings: {install_process.stderr}"
            )
            # Continue anyway - some packages might still work
        
    except Exception as e:
        print_error(f"Failed to install requirements: {e}")
        log_error(logger, f"Failed to install requirements: {e}")
        print_info("You may need to install packages manually")


def repair_environment():
    """Force recreate the virtual environment and reinstall packages."""
    print_step(1, 3, "Repairing environment...")
    create_virtualenv()
    check_and_install_requirements()
    print_success("Repair complete. Relaunching app...")

def run_app():
    """Launch the main application."""
    print_step(4, 4, "Launching application...")
    
    venv_python = Path(__file__).parent / "venv" / "Scripts" / "python.exe"
    if not venv_python.exists():
        venv_python = Path(__file__).parent / "venv" / "bin" / "python3"
        
    app_file = Path(__file__).parent / "kyo_qa_tool_app.py"
    
    spinner = ConsoleSpinner()
    spinner.start("Starting KYO QA ServiceNow Knowledge Tool...")
    
    try:
        time.sleep(1)  # Small pause for visual effect
        spinner.stop("Application ready!")
        log_info(logger, f"Launching main app: {app_file}")
        
        # Print a final message
        print("\n" + "=" * 70)
        print(
            f"{COLOR_SUCCESS}KYO QA ServiceNow Knowledge Tool {VERSION} is "
            f"starting...{COLOR_RESET}"
        )
        print("=" * 70 + "\n")
        
        # Launch the application
        subprocess.run([str(venv_python), str(app_file)], check=True)
        
    except subprocess.CalledProcessError as e:
        spinner.stop()
        print_error(f"Application failed to start: {e}")
        log_error(logger, f"Application failed to start: {e}")
        sys.exit(1)
    except Exception as e:
        spinner.stop()
        print_error(f"Failed to launch application: {e}")
        log_error(logger, f"Failed to launch application: {e}")
        sys.exit(1)

def main(cli_args=None):
    """Main setup and launch sequence with smart environment checking."""
    try:
        args = parse_arguments(cli_args)
        print_header()

        if args.repair:
            repair_environment()
        
        # Always check Python version
        check_python_version()
        
        # Smart environment checking
        venv_exists = check_existing_virtualenv()
        
        if not venv_exists:
            create_virtualenv()
        
        # Always check and install missing requirements
        check_and_install_requirements()
        
        # Launch the application
        run_app()
        
        log_info(logger, "Setup and launch complete. Exiting normally.")
        
    except KeyboardInterrupt:
        print(f"\n{COLOR_WARNING}Setup interrupted by user.{COLOR_RESET}")
        log_warning(logger, "Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        log_error(logger, f"Unexpected setup error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
