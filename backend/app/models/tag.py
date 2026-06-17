from sqlalchemy import Column, String, Table, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


# Many-to-many association table between posts and tags
post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", String, ForeignKey("posts.id"), primary_key=True),
    Column("tag_id", String, ForeignKey("tags.id"), primary_key=True),
)


class Tag(Base):
    __tablename__ = "tags"

    id = Column(String, primary_key=True)
    name = Column(String, unique=True, nullable=False)  # e.g. "python", "fastapi"

    # Relationships
    posts = relationship("Post", secondary=post_tags, back_populates="tags")
