from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, field_validator
import nh3


# ── Request Schemas (what the admin sends) ────────────────────────────────────

class PostCreate(BaseModel):
    title: str
    content: str                          # Rich HTML from TipTap editor
    excerpt: Optional[str] = None         # Short summary for listing page
    cover_image: Optional[str] = None     # Cloudinary URL of the hero image
    github_repo_url: Optional[str] = None # Linked GitHub repo
    tags: Optional[List[str]] = []        # Tag names e.g. ["python", "fastapi"]

    @field_validator("content")
    @classmethod
    def sanitize_content(cls, v: str) -> str:
        """Strip malicious scripts from HTML before saving to DB (XSS prevention)."""
        return nh3.clean(
            v,
            tags={
                # Text formatting
                "p", "br", "strong", "em", "u", "s", "blockquote",
                # Headings
                "h1", "h2", "h3", "h4", "h5", "h6",
                # Lists
                "ul", "ol", "li",
                # Code
                "pre", "code",
                # Media
                "img", "a",
                # Layout
                "hr", "div", "span",
            },
            attributes={
                "img": {"src", "alt", "width", "height"},
                "a": {"href", "target", "rel"},
                "code": {"class"},   # needed for language-python etc.
                "pre": {"class"},
                "div": {"class"},
                "span": {"class"},
            },
        )

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
        return nh3.clean(
            v,
            tags={
                "p", "br", "strong", "em", "u", "s", "blockquote",
                "h1", "h2", "h3", "h4", "h5", "h6",
                "ul", "ol", "li",
                "pre", "code",
                "img", "a",
                "hr", "div", "span",
            },
            attributes={
                "img": {"src", "alt", "width", "height"},
                "a": {"href", "target", "rel"},
                "code": {"class"},
                "pre": {"class"},
                "div": {"class"},
                "span": {"class"},
            },
        )

    @field_validator("tags", mode="before")
    @classmethod
    def lowercase_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        return [tag.strip().lower() for tag in v if tag.strip()]


# ── Response Schemas (what the API sends back) ────────────────────────────────

class TagResponse(BaseModel):
    name: str

    model_config = {"from_attributes": True}


class PostResponse(BaseModel):
    id: str
    title: str
    slug: str
    excerpt: Optional[str]
    content: str
    cover_image: Optional[str]
    published: bool
    github_repo_url: Optional[str]
    tags: List[str]                      # Return just tag names, not full objects
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}

    @field_validator("tags", mode="before")
    @classmethod
    def extract_tag_names(cls, v) -> List[str]:
        """Convert Tag objects from SQLAlchemy into plain strings."""
        if v and hasattr(v[0], "name"):
            return [tag.name for tag in v]
        return v


class PostSummary(BaseModel):
    """Lightweight version for listing pages — no full content."""
    id: str
    title: str
    slug: str
    excerpt: Optional[str]
    cover_image: Optional[str]
    published: bool
    github_repo_url: Optional[str]
    tags: List[str]
    created_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("tags", mode="before")
    @classmethod
    def extract_tag_names(cls, v) -> List[str]:
        if v and len(v) > 0 and hasattr(v[0], "name"):
            return [tag.name for tag in v]
        return v
