import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from slugify import slugify
from sqlalchemy.orm import Session

from app.auth.jwt import require_admin
from app.core.database import get_db
from app.models.post import Post
from app.models.tag import Tag
from app.schemas.post import PostCreate, PostUpdate, PostResponse, PostSummary

router = APIRouter(prefix="/admin/posts", tags=["admin"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_or_create_tags(tag_names: List[str], db: Session) -> List[Tag]:
    """
    For each tag name, fetch it from DB if it exists or create it if not.
    Prevents duplicate tags like two rows both named 'python'.
    """
    tags = []
    for name in tag_names:
        tag = db.query(Tag).filter(Tag.name == name).first()
        if not tag:
            tag = Tag(id=str(uuid.uuid4()), name=name)
            db.add(tag)
        tags.append(tag)
    return tags


def unique_slug(title: str, db: Session, exclude_id: Optional[str] = None) -> str:
    """
    Generate a URL-safe slug from the title.
    Appends a short unique suffix if the slug already exists.
    e.g. 'my-post' → 'my-post-a1b2' if 'my-post' is taken.
    """
    base_slug = slugify(title)
    slug = base_slug
    query = db.query(Post).filter(Post.slug == slug)
    if exclude_id:
        query = query.filter(Post.id != exclude_id)
    if query.first():
        slug = f"{base_slug}-{str(uuid.uuid4())[:4]}"
    return slug


# ── Admin Endpoints (all require admin JWT) ───────────────────────────────────

@router.get("/", response_model=List[PostSummary])
def list_all_posts(
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    """Dashboard — returns ALL posts including drafts, ordered by newest first."""
    return db.query(Post).order_by(Post.created_at.desc()).all()


@router.get("/{post_id}", response_model=PostResponse)
def get_post_by_id(
    post_id: str,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    """Fetch a single post by ID (draft or published) for the edit page."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post


@router.post("/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
def create_post(
    body: PostCreate,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    """
    Create a new post. Always saved as a draft first (published=False).
    Use PATCH /{id}/publish to make it live.
    """
    slug = unique_slug(body.title, db)
    tags = get_or_create_tags(body.tags or [], db)

    post = Post(
        id=str(uuid.uuid4()),
        title=body.title,
        slug=slug,
        excerpt=body.excerpt,
        content=body.content,
        cover_image=body.cover_image,
        github_repo_url=body.github_repo_url,
        published=False,
        tags=tags,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


@router.put("/{post_id}", response_model=PostResponse)
def update_post(
    post_id: str,
    body: PostUpdate,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    """
    Update any field on a post — title, content (with images/code), tags, etc.
    Only the fields you send will be updated.
    """
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    if body.title is not None:
        post.title = body.title
        post.slug = unique_slug(body.title, db, exclude_id=post_id)
    if body.content is not None:
        post.content = body.content
    if body.excerpt is not None:
        post.excerpt = body.excerpt
    if body.cover_image is not None:
        post.cover_image = body.cover_image
    if body.github_repo_url is not None:
        post.github_repo_url = body.github_repo_url
    if body.tags is not None:
        post.tags = get_or_create_tags(body.tags, db)

    db.commit()
    db.refresh(post)
    return post


@router.patch("/{post_id}/publish", response_model=PostResponse)
def toggle_publish(
    post_id: str,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    """
    Toggle a post between draft and published.
    Draft → Published, Published → Draft.
    """
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    
    post.published = not post.published
    db.commit()
    db.refresh(post)
    return post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: str,
    db: Session = Depends(get_db),
    admin: dict = Depends(require_admin),
):
    """Permanently delete a post and all its tag associations."""
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    db.delete(post)
    db.commit()
