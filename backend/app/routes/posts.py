from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.post import Post
from app.models.tag import Tag
from app.schemas.post import PostResponse, PostSummary

router = APIRouter(prefix="/posts", tags=["posts"])


# ── Public Endpoints (no auth required) ──────────────────────────────────────

@router.get("/", response_model=List[PostSummary])
def list_posts(tag: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Returns all published posts as summaries (no full content).
    Optionally filter by tag: GET /posts?tag=python
    """
    query = db.query(Post).filter(Post.published == True)
    if tag:
        query = query.join(Post.tags).filter(Tag.name == tag.lower())
    posts = query.order_by(Post.created_at.desc()).all()
    return posts


@router.get("/{slug}", response_model=PostResponse)
def get_post(slug: str, db: Session = Depends(get_db)):
    """
    Returns the full content of a single published post by its slug.
    e.g. GET /posts/how-i-built-this-blog
    """
    post = db.query(Post).filter(Post.slug == slug, Post.published == True).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post
