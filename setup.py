import subprocess
import sys
import os

def run_command(command):
    print(f"Running: {' '.join(command)}")
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e}")
        sys.exit(1)

def main():
    print("Initializing GeoGuessr Bot Environment...")

    # Install dependencies from requirements.txt
    if os.path.exists("requirements.txt"):
        print("\n--- Installing dependencies from requirements.txt ---")
        run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    else:
        print("\nWarning: requirements.txt not found. Skipping pip install.")

    # Install Playwright browsers
    print("\n--- Installing Playwright browsers ---")
    run_command([sys.executable, "-m", "playwright", "install", "chromium"])

    # Check for .env file
    if not os.path.exists(".env"):
        print("\nWarning: .env file not found. Please create one based on .env.example (if available) or add your GEOGUESSR_COOKIE.")
    else:
        print("\n.env file detected.")

    print("\nSetup complete! You can now run the bot using 'python main.py'.")

if __name__ == "__main__":
    main()
