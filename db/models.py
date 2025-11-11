from sqlalchemy import Column, Integer, String, ForeignKey, Date, Numeric, Boolean, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()