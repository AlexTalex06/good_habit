
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy.sql import func

DBSession = scoped_session(sessionmaker())
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(150), nullable=False)

    habits = relationship("Habit", back_populates="user", cascade="all, delete-orphan")

class Habit(Base):
    __tablename__ = 'habits'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, default='')
    difficulty = Column(String(20), default='medium')
    frequency = Column(String(20), default='Diario')
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="habits")
    progress = relationship("HabitProgress", back_populates="habit", cascade="all, delete-orphan", passive_deletes=True)

class HabitProgress(Base):
    __tablename__ = 'habit_progress'

    id = Column(Integer, primary_key=True)
    habit_id = Column(Integer, ForeignKey('habits.id', ondelete='CASCADE'), nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now())

    habit = relationship("Habit", back_populates="progress")
