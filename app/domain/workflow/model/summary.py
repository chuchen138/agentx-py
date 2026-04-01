from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class Summary(Base):
    __tablename__ = "summaries"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    summary_id = Column(String, unique=True, nullable=False, index=True)
    session_id = Column(String, nullable=False, index=True)
    workflow_id = Column(String, ForeignKey("workflows.workflow_id"), nullable=True)
    summary_text = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    workflow = relationship("Workflow", backref="summaries")
    
    def __repr__(self):
        return f"<Summary(id={self.id}, summary_id={self.summary_id}, session_id={self.session_id})>"
