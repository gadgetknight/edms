# models/user_models.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from .base_model import BaseModel


class User(BaseModel):
    """User table for login and authentication"""

    __tablename__ = "users"

    user_id = Column(String(20), primary_key=True)
    password_hash = Column(String(255), nullable=False)
    user_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    printer_id = Column(String(20))
    default_screen_colors = Column(String(100))


class SystemConfig(BaseModel):
    """System configuration parameters"""

    __tablename__ = "system_config"

    config_key = Column(String(50), primary_key=True)
    config_value = Column(String(255))
    description = Column(String(255))
