import time
import subprocess
import datetime
import os
import json
import pytesseract
from PIL import Image
from openai import OpenAI  # Import the new client-based API

# Instantiate an OpenAI client.
# Make sure your environment variable OPENAI_API_KEY is set, or assign the key directly.
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# Alternatively, you could uncomment the next line and set your key directly:
# client = OpenAI(api_key="your-api-key-here")

# Configuration
interval = 5 * 60  # 5 minutes
save_dir = os.path.expanduser("~/productivity/screenshots")
log_file = os.path.expanduser("~/productivity/summary_log.json")

# Ensure directories exist
if not os.path.exists(save_dir):
    os.makedirs(save_dir)


def summarize_text(text):
    try:
        prompt = (
            f"Summarize the contents of the following screenshot text:\n\n"
            f"{text}\n\n"
            "Summary:"
        )
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "Summaraize the text."},
                      {"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return "Summary generation failed"


def analyze_image(image_path):
    """
    Extracts text from a screenshot using OCR and categorizes it.
    """
    try:
        image = Image.open(image_path)
        extracted_text = pytesseract.image_to_string(image)
    except Exception as e:
        return {"text": "Error during OCR", "category": "Error"}

    if not extracted_text.strip():
        return {"text": "No text detected", "category": "Idle/Empty Screen"}

    # Categorize content
    category = categorize_content(extracted_text)
    summary = summarize_text(extracted_text)

    return {"text": summary, "category": category}


def get_active_application():
    """
    Uses AppleScript to get the currently active application name on macOS.
    """
    try:
        result = subprocess.run(
            ["osascript", "-e", 'tell application "System Events" to get name of application processes whose frontmost is true'],
            capture_output=True,
            text=True
        )
        return result.stdout.strip() or "Unknown"
    except Exception:
        return "Unknown"


def categorize_content(text):
    """
    Uses OpenAI to categorize the extracted text into a predefined category.
    """
    categories = ["Work", "Communication", "Browsing",
                  "Entertainment", "Idle/Empty Screen"]
    vety = ', '.join(categories)
    prompt = (
        "Categorize the following text into one of the categories: "
        + ", ".join(categories)
        + ".\n\nText:\n"
        + text
        + "\n\nCategory:"
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "You are a classifier that categorizes user activity based on what you see on the user's screen."},
                      {"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return "Uncategorized"


def log_summary(data):
    """
    Logs structured data to a JSON file safely.
    """
    try:
        logs = []
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                try:
                    logs = json.load(f)  # Load existing logs
                except json.JSONDecodeError:
                    logs = []  # Reset if file is corrupt

        logs.append(data)

        # Safely write the JSON data
        with open(log_file, "w") as f:
            json.dump(logs, f, indent=4)

    except Exception as e:
        print(f"Error logging data: {e}")


def main():
    print(f"Temporary screenshot storage: {save_dir}")
    print(f"Summaries will be logged to: {log_file}")
    # print(f"Taking a screenshot every {interval / 60} minutes. Press Ctrl+C to stop.")

    try:
        while True:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = os.path.join(save_dir, f"screenshot_{timestamp}.png")

            # Get active application name
            active_app = get_active_application()

            # Capture a screenshot
            subprocess.run(["screencapture", "-x", filename])
            print(f"\nCaptured screenshot: {filename}")

            # Analyze image and categorize content
            analysis = analyze_image(filename)
            summary_text = analysis["text"]
            category = analysis["category"]

            # Log structured data
            log_entry = {
                "timestamp": timestamp,
                "application": active_app,
                "screenshot": filename,
                "summary": summary_text,
                "category": category,
            }
            log_summary(log_entry)

            print(f"Summary ({category} - {active_app}):\n{summary_text}\n")
            print(f"Logged to: {log_file}")

            # Delete the screenshot after processing
            os.remove(filename)

            # Wait for next cycle
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nScreenshot capture stopped.")


if __name__ == "__main__":
    main()
