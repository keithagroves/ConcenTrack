import time
import subprocess
import datetime
import os
import pytesseract
from PIL import Image
from openai import OpenAI  # Import the new client-based API

# Instantiate an OpenAI client.
# Make sure your environment variable OPENAI_API_KEY is set, or assign the key directly.
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# Alternatively, you could uncomment the next line and set your key directly:
# client = OpenAI(api_key="your-api-key-here")

# Configuration: adjust the interval (in seconds) as needed.
interval = 5 * 60  # 5 minutes

# Directory to temporarily save screenshots.
save_dir = os.path.expanduser("~/screenshots")
if not os.path.exists(save_dir):
    os.makedirs(save_dir)


def analyze_image(image_path):
    """
    Uses OCR to extract text from the image and then calls the OpenAI API
    to generate a summary of the extracted text.
    """
    try:
        # Open the image and use pytesseract to extract text.
        image = Image.open(image_path)
        extracted_text = pytesseract.image_to_string(image)
    except Exception as e:
        return f"Error during OCR: {e}"

    # If no text is detected, note that in the summary.
    if not extracted_text.strip():
        return "No text detected in the screenshot."

    # Create a prompt for the model to summarize the extracted text.
    prompt = (
        f"Summarize the contents of the following screenshot text:\n\n"
        f"{extracted_text}\n\n"
        "Summary:"
    )

    try:
        # Call the new API method using the client instance.
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # or use "gpt-4" if you have access.
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that summarizes screenshot content."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        # Extract and return the summary from the response.
        summary = response.choices[0].message.content.strip()
        return summary
    except Exception as e:
        return f"Error during OpenAI API call: {e}"


def main():
    print(f"Temporary screenshot storage: {save_dir}")
    print(f"Taking a screenshot every {
          interval / 60} minutes. Press Ctrl+C to stop.")

    try:
        while True:
            # Generate a filename with a timestamp.
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = os.path.join(save_dir, f"screenshot_{timestamp}.png")

            # Take a screenshot using macOS's built-in screencapture (the -x flag suppresses sound).
            subprocess.run(["screencapture", "-x", filename])
            print(f"\nCaptured screenshot: {filename}")

            # Analyze the screenshot with OCR and the OpenAI API.
            summary = analyze_image(filename)
            print(f"Summary:\n{summary}\n")

            # Delete the screenshot file.
            try:
                os.remove(filename)
                print(f"Deleted screenshot: {filename}")
            except Exception as e:
                print(f"Error deleting screenshot: {e}")

            # Wait for the specified interval before taking the next screenshot.
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nScreenshot capture stopped.")


if __name__ == "__main__":
    main()
