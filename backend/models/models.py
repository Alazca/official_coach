"""
Core data models for AI Weightlifting Assistant.

This module defines all Pydantic models used throughout the application,
ensuring type safety and validation.
"""

from pydantic import BaseModel, EmailStr, field_validator, Field
from enum import Enum
import re
from datetime import date
from typing import Optional, List, Dict, Any, Union


class Gender(str, Enum):
    """User gender options."""

    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"


class ActivityLevel(str, Enum):
    """User activity level classification."""

    SEDENTARY = "Sedentary"  # Very little physical activity
    CASUAL = "Casual"  # Light activity 1-2 days per week
    MODERATE = "Moderate"  # Moderate activity 2-3 days per week
    ACTIVE = "Active"  # Intense activity 3-5 days per week
    INTENSE = "Intense"  # Very intense activity 5-7 days per week


class Source(str, Enum):
    """Data source classification."""

    MANUAL = "Manual"  # User entered data
    AUTO = "Auto"  # System generated data
    COACH = "Coach"  # Coach entered data


class GoalType(str, Enum):
    """Types of fitness goals."""

    STRENGTH = "Strength"  # Focus on strength gains
    ENDURANCE = "Endurance"  # Focus on endurance/stamina
    WEIGHT_LOSS = "Weight-Loss"  # Focus on body composition
    PERFORMANCE = "Performance"  # Focus on specific performance metrics
    DEFAULT = "Default"  # Balanced approach


class StrengthDimension(str, Enum):
    """Dimensions of strength for tracking and analysis."""

    MAXIMAL_STRENGTH = "Maximal_strength"  # 1RM capacity
    RELATIVE_STRENGTH = "Relative_strength"  # Strength relative to bodyweight
    EXPLOSIVE_STRENGTH = "Explosive_strength"  # Power development
    STRENGTH_ENDURANCE = "Strength_endurance"  # Rep capacity at moderate load
    AGILE_STRENGTH = "Agile_strength"  # Quick direction changes
    SPEED_STRENGTH = "Speed_strength"  # Force at high velocity
    STARTING_STRENGTH = "Starting_strength"  # Initial force production


class ConditioningDimension(str, Enum):
    """Dimensions of conditioning for tracking and analysis."""

    CARDIOVASCULAR_ENDURANCE = "Cardiovascular_endurance"  # Aerobic capacity
    MUSCLE_STRENGTH = "Muscle_strength"  # Raw strength
    MUSCLE_ENDURANCE = "Muscle_endurance"  # Work capacity
    FLEXIBILITY = "Flexibility"  # Range of motion
    BODY_COMPOSITION = "Body_composition"  # Lean mass ratio


class UserLogin(BaseModel):
    """User login credentials."""

    email: EmailStr
    password: str


class ReadinessScore(BaseModel):
    """Daily readiness score tracking."""

    user_id: int
    readiness_score: int = Field(ge=0, le=100)
    contributing_factors: str  # JSON-serialized factors
    readiness_date: date
    source: Source = Source.AUTO
    alignment_score: float = Field(default=0.0, ge=0.0, le=1.0)
    overtraining_score: float = Field(default=0.0, ge=0.0, le=1.0)


class UserGoal(BaseModel):
    """User fitness goal tracking."""

    user_id: int
    goal_type: GoalType
    description: str
    target_date: date


class DailyCheckIn(BaseModel):
    """Daily user wellness check-in data."""

    weight: int  # Weight in kg or lbs (units handled in UI)
    sleep: int  # Sleep quality 1-10
    stress: int  # Stress level 1-10
    energy: int  # Energy level 1-10
    soreness: int  # Soreness level 1-10

    @field_validator("weight")
    def validate_weight(cls, v):
        """Validate weight is a positive integer."""
        if not isinstance(v, int):
            raise ValueError("Weight must be an integer")
        if v < 0:
            raise ValueError("Weight must be greater than 0")
        return v

    @field_validator("sleep", "stress", "energy", "soreness")
    def validate_rating(cls, v, info):
        """Validate 1-10 scale metrics are within range."""
        field_name = info.field_name
        if v < 1 or v > 10:
            raise ValueError(f"{field_name.capitalize()} must be between 1 and 10")
        return v


class UserRegistration(BaseModel):
    """New user registration data."""

    email: EmailStr
    password: str
    name: str
    gender: Gender
    dob: date
    height: float = Field(gt=0)
    weight: float = Field(gt=0)
    initialActivityLevel: ActivityLevel
    goal: GoalType

    @field_validator("password")
    def validate_password(cls, v):
        """Validate password meets security requirements."""
        if len(v) < 8:
            raise ValueError("Password too short")

        # Check for at least one letter
        if not re.search(r"[a-zA-Z]", v):
            raise ValueError("Password must contain at least one letter")

        # Check for at least one digit
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")

        # Check for at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")

        return v


class VectorData(BaseModel):
    """Vector representation with dimensions and values."""

    dimensions: List[str]
    vector: List[float]
    created_at: Optional[str] = None


class UserVector(VectorData):
    """User vector with fitness metrics."""

    user_id: int
    profile_name: str = "default"
    activity_level: Optional[str] = None
    final_scalar: Optional[float] = None
    influence_scalars: Optional[Dict[str, float]] = None


class TargetVector(VectorData):
    """Target vector representing fitness goals."""

    target_id: Optional[int] = None
    user_id: int
    goal_type: GoalType
    profile_name: str = "default"
    target_date: date
    milestones: Optional[List[Dict[str, Any]]] = None


class MilestoneVector(VectorData):
    """Milestone vector for progress tracking."""

    percent: int  # Percent of progress to final goal
    date: date
    is_final: bool = False
    is_prorated: bool = False
    is_initial: bool = False


class GoalProgress(BaseModel):
    """Goal progress tracking and metrics."""

    target_id: int
    goal_type: GoalType
    time_progress_pct: float = Field(ge=0.0, le=100.0)
    vector_progress_pct: float = Field(ge=0.0, le=100.0)
    on_track: bool
    days_passed: int
    days_remaining: int
    total_days: int
    current_milestone_pct: float = Field(ge=0.0, le=100.0)
    dimension_progress: List[Dict[str, Any]]
    target_date: date


class StrengthMetrics(BaseModel):
    """Raw strength performance metrics."""

    combined_strength: float  # Combined relative strength metric
    total_volume: float  # Total volume over period
    volume_percentile: float  # Percentile rank among users


class ConditioningMetrics(BaseModel):
    """Raw conditioning performance metrics."""

    weekly_volume: float  # Total weekly volume
    training_days: int  # Number of training days
    volume_change_pct: float  # Percent change vs prior period
    intensity_avg: float  # Average intensity (volume/reps)
    consistency_pct: float  # Consistency of volume


class InfluenceScalars(BaseModel):
    """Normalized fitness influence factors."""

    combined_strength: float = Field(ge=0.0, le=1.0)
    total_volume: float = Field(ge=0.0, le=1.0)
    volume_percentile: float = Field(ge=0.0, le=1.0)
    weekly_volume: float = Field(ge=0.0, le=1.0)
    training_days: float = Field(ge=0.0, le=1.0)
    volume_change_pct: float = Field(ge=0.0, le=1.0)
    intensity_avg: float = Field(ge=0.0, le=1.0)
    consistency_pct: float = Field(ge=0.0, le=1.0)
    influence_scalar: float = Field(ge=0.0, le=1.0)
