import cloudinary

from app.core.config import settings

# Initialize Cloudinary with credentials from .env
# This runs once when the module is first imported
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,  # Always use HTTPS URLs
)
