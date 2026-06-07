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

    # Sync dependencies via uv
    print("\n--- Installing dependencies via uv ---")
    run_command(["uv", "sync"])

    # Install Playwright browsers
    print("\n--- Installing Playwright browsers ---")
    run_command(["uv", "run", "playwright", "install", "chromium"])

    # Check for .env file
    if not os.path.exists(".env"):
        print("\nWarning: .env file not found. Please create one and add your GEOGUESSR_COOKIE.")
    else:
        print("\n.env file detected.")

    print("\nSetup complete! You can now run the bot using 'uv run python main.py'.")

if __name__ == "__main__":
    main()
