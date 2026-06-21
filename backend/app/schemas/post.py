from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, field_validator
import nh3

# Allowed HTML tags and attributes for sanitization
_ALLOWED_TAGS = {
    "p", "br", "strong", "em", "u", "s", "blockquote",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "ul", "ol", "li",
    "pre", "code",
    "img", "a",
    "hr", "div", "span",
}
_ALLOWED_ATTRS = {
    "img": {"src", "alt", "width", "height"},
    "a": {"href", "target"},
    "code": {"class"},
    "pre": {"class"},
    "div": {"class"},
    "span": {"class"},
}


def _sanitize(html: str) -> str:
    """Strip malicious scripts from HTML (XSS prevention)."""
    return nh3.clean(html, tags=_ALLOWED_TAGS, attributes=_ALLOWED_ATTRS)


# ── Request Schemas (what the admin sends) ────────────────────────────────────

class PostCreate(BaseModel):
    title: str
    content: str                           # Rich HTML from TipTap editor
    excerpt: Optional[str] = None          # Short summary for listing page
    cover_image: Optional[str] = None      # Cloudinary URL of the hero image
    github_repo_url: Optional[str] = None  # Linked GitHub repo
    tags: List[str] = []                   # Tag names e.g. ["python", "fastapi"]

    @field_validator("content")
    @classmethod
    def sanitize_content(cls, v: str) -> str:
        return _sanitize(v)

    @field_validator("tags")
    @classmethod
    def lowercase_tags(cls, v: List[str]) -> List[str]:
        """Normalize tags to lowercase to avoid duplicates like 'Python' vs 'python'."""
        return [tag.strip().lower() for tag in v if tag.strip()]


class PostUpdate(BaseModel):
    """All fields optional — only send what you want to change."""
    title: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    cover_image: Optional[str] = None
    github_repo_url: Optional[str] = None
    tags: Optional[List[str]] = None

    @field_validator("content", mode="before")
    @classmethod
    def sanitize_content(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return _sanitize(v)

    @field_validator("tags", mode="before")
    @classmethod
    def lowercase_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        return [tag.strip().lower() for tag in v if tag.strip()]


# ── Response Schemas (what the API sends back) ────────────────────────────────

class PostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    slug: str
    excerpt: Optional[str] = None
    content: str
    cover_image: Optional[str] = None
    published: bool
    github_repo_url: Optional[str] = None
    tags: List[str] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    @field_validator("tags", mode="before")
    @classmethod
    def extract_tag_names(cls, v) -> List[str]:
        """Convert SQLAlchemy Tag objects into plain strings."""
        if v and len(v) > 0 and hasattr(v[0], "name"):
            return [tag.name for tag in v]
        return list(v) if v else []


class PostSummary(BaseModel):
    """Lightweight version for listing pages — no full content."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    slug: str
    excerpt: Optional[str] = None
    cover_image: Optional[str] = None
    published: bool
    github_repo_url: Optional[str] = None
    tags: List[str] = []
    created_at: datetime

    @field_validator("tags", mode="before")
    @classmethod
    def extract_tag_names(cls, v) -> List[str]:
        if v and len(v) > 0 and hasattr(v[0], "name"):
            return [tag.name for tag in v]
        return list(v) if v else []
