from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base
from app.models.tag import post_tags


class Post(Base):
    __tablename__ = "posts"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)      # URL-friendly e.g. "how-i-built-fastapi-blog"
    excerpt = Column(String, nullable=True)                 # Short summary shown on listing page
    content = Column(Text, nullable=False)                  # Full rich-text HTML content
    cover_image = Column(String, nullable=True)             # Cloudinary image URL
    published = Column(Boolean, default=False)              # False = draft, True = live
    github_repo_url = Column(String, nullable=True)         # Linked GitHub repo URL

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    tags = relationship("Tag", secondary=post_tags, back_populates="posts")
