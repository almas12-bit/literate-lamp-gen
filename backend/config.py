import os
import sys

# Directory detection for frozen (PyInstaller executable) vs standard python execution
if getattr(sys, "frozen", False):
    # Running as compiled PyInstaller executable
    APP_DIR = os.path.dirname(sys.executable)
    BUNDLE_DIR = getattr(sys, "_MEIPASS", APP_DIR)
else:
    # Running in standard source / dev mode
    APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    BUNDLE_DIR = APP_DIR

# Portable binaries folder (e.g. ffmpeg, ghostscript)
BIN_DIR = os.path.join(APP_DIR, "bin")

# Prepend BIN_DIR to PATH if it exists so external tools can be invoked directly
if os.path.isdir(BIN_DIR):
    os.environ["PATH"] = BIN_DIR + os.pathsep + os.environ.get("PATH", "")

GEMINI_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-flash-lite-latest",
    "gemini-3.1-flash-lite",
    "gemini-3.8-flash",
]

SS_CATEGORIES = [
    "Abstract","Animals/Wildlife","Arts","Backgrounds/Textures","Beauty/Fashion",
    "Buildings/Landmarks","Business/Finance","Celebrities","Education","Food and drink",
    "Healthcare/Medical","Holidays","Industrial","Interiors","Miscellaneous",
    "Nature","Objects","Parks/Outdoor","People","Religion","Science",
    "Signs/Symbols","Sports/Recreation","Technology","Transportation","Vintage"
]

AS_CATEGORIES = {
    1: "Animals", 2: "Buildings and Architecture", 3: "Business",
    4: "Drinks", 5: "The Environment", 6: "States of Mind",
    7: "Food", 8: "Graphic Resources", 9: "Hobbies and Leisure",
    10: "Industry", 11: "Landscapes", 12: "Lifestyle",
    13: "People", 14: "Plants and Flowers", 15: "Culture and Religion",
    16: "Science", 17: "Social Issues", 18: "Sports",
    19: "Technology", 20: "Transport", 21: "Travel"
}

GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"
VIDEO_FRAME_COUNT = 3
DEFAULT_KEYWORD_COUNT = 45
MIN_KEYWORD_COUNT = 15
MAX_KEYWORD_COUNT = 49
