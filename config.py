import os

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# # Image directory
# IMAGE_FOLDER = r"C:\Users\asmit\OneDrive\Desktop\MOS-AS-2\pikwizard_images"
IMAGE_FOLDER =  os.path.join(os.path.dirname(__file__), "pikwizard_images")
# METADATA_FILE = os.path.join(IMAGE_FOLDER, "\metadata.json")
METADATA_FILE = os.path.join(os.path.dirname(__file__), "pikwizard_images/metadata.json")

# Flask configuration
class Config:
    SECRET_KEY = 'your-secret-key-here'
    IMAGE_FOLDER = os.path.join(os.path.dirname(__file__), "pikwizard_images")
    THUMBNAIL_FOLDER = os.path.join(BASE_DIR, 'static', 'thumbnails')
    PER_PAGE = 50  # Images per page