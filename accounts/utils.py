# accounts/utils.py
import io
import random

from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont

# CONSTANTS FOR COLORS
COLOR_SLATE_GRAY = (73, 80, 87)
COLOR_DARK_CHARCOAL = (33, 37, 41)
COLOR_LIGHT_GRAY = (134, 142, 150)
COLOR_VIBRANT_PURPLE = (190, 75, 219)
COLOR_BRIGHT_BLUE = (28, 126, 214)
COLOR_TEAL_GREEN = (32, 201, 151)

AVATAR_BG_COLORS = [
    COLOR_SLATE_GRAY,
    COLOR_DARK_CHARCOAL,
    COLOR_LIGHT_GRAY,
    COLOR_VIBRANT_PURPLE,
    COLOR_BRIGHT_BLUE,
    COLOR_TEAL_GREEN,
]

# CONSTANTS FOR THE AVATAR
AVATAR_HEIGHT = 200
AVATAR_WIDTH = 200
AVATAR_FONT_FAMILY = "arial.ttf"
AVATAR_FONT_SIZE = 100
AVATAR_FILE_FORMAT = "PNG"


def generate_avatar_file(username, email):
    """
    Generates a default avatar image with the first letter of the username
    on a random colored background.
    """
    size = (AVATAR_HEIGHT, AVATAR_WIDTH)
    bg_color = random.choice(AVATAR_BG_COLORS)

    image = Image.new("RGB", size, color=bg_color)
    draw = ImageDraw.Draw(image)

    # Get the first letter of the username, or 'U' if empty
    first_letter = username[0].upper() if username else "U"

    try:
        font = ImageFont.truetype(AVATAR_FONT_FAMILY, AVATAR_FONT_SIZE)
    except IOError:
        # Fallback to default font if arial.ttf is not available on the system
        font = ImageFont.load_default()

    w, h = size

    # Calculate text bounding box to center it
    bbox = draw.textbbox((0, 0), first_letter, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Calculate position for exact center
    position = ((w - text_width) // 2, (h - text_height) // 2 - bbox[1])

    # Draw the text on the image
    draw.text(position, first_letter, fill="white", font=font)

    # Save to a bytes buffer
    buffer = io.BytesIO()
    image.save(buffer, format=AVATAR_FILE_FORMAT)

    # Generate a unique filename based on email
    filename = f"avatar_{email.split('@')[0]}.png"
    return ContentFile(buffer.getvalue(), name=filename)
