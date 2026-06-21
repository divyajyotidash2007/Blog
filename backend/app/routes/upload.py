import cloudinary.uploader
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status

import app.core.cloudinary  # noqa: F401 — triggers cloudinary.config() on import
from app.auth.jwt import require_admin

router = APIRouter(prefix="/upload", tags=["upload"])

# Allowed image MIME types
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}

# Max file size: 5MB
MAX_SIZE_BYTES = 5 * 1024 * 1024


@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    admin: dict = Depends(require_admin),
):
    """
    Upload an image to Cloudinary and return its public URL.

    Called by the TipTap editor whenever you insert an image into a post.
    The returned URL gets embedded directly into the post's HTML content.

    - Accepts: JPEG, PNG, WebP, GIF
    - Max size: 5MB
    - Images are stored in the 'blog/' folder on Cloudinary
    """
    # Validate file type
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type '{file.content_type}'. Allowed: JPEG, PNG, WebP, GIF",
        )

    # Read file and validate size
    contents = await file.read()
    if len(contents) > MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is 5MB, got {len(contents) / 1024 / 1024:.1f}MB",
        )

    # Upload to Cloudinary
    try:
        result = cloudinary.uploader.upload(
            contents,
            folder="blog",                  # stored under blog/ in your Cloudinary account
            resource_type="image",
            transformation=[
                {"quality": "auto"},        # auto-optimize quality
                {"fetch_format": "auto"},   # serve WebP to browsers that support it
            ],
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Cloudinary upload failed: {str(e)}",
        )

    return {
        "url": result["secure_url"],        # HTTPS URL to embed in the post
        "public_id": result["public_id"],   # Cloudinary ID (useful for deletion later)
        "width": result.get("width"),
        "height": result.get("height"),
    }
