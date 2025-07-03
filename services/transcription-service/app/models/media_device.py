"""Media device model definition."""
from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class MediaDevice(Base):
    """Media device model for storing detected devices."""
    __tablename__ = "media_devices"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)  # Reference to User service
    
    # Device information
    device_id = Column(String(255), nullable=False)  # System device ID
    device_name = Column(String(255), nullable=False)
    device_type = Column(String(20), nullable=False)  # audio, video
    
    # Device capabilities
    capabilities = Column(JSON, nullable=True)  # {sample_rates: [], formats: []}
    is_default = Column(Boolean, default=False)
    is_available = Column(Boolean, default=True)
    
    # Detection metadata
    detected_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<MediaDevice(id={self.id}, name={self.device_name}, type={self.device_type})>"
