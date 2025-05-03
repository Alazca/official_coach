from pydantic import BaseModel, EmailStr, field_validator
from enum import Enum
import re
from datetime import date


class Gender(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"


class ActivityLevel(str, Enum):
    SEDENTARY = "Sedentary"
    CASUAL = "Casual"
    MODERATE = "Moderate"
    ACTIVE = "Active"
    INTENSE = "Intense"


class Source(str, Enum):
    MANUAL = "Manual"
    AUTO = "Auto"
    COACH = "Coach"


class GoalType(str, Enum):
    STRENGTH = "Strength"
    ENDURANCE = "Endurance"
    WEIGHT_LOSS = "Weight-Loss"
    PERFORMANCE = "Performance"
    DEFAULT = "Default"


class StrengthDimension(str, Enum):
    MAXIMAL_STRENGTH = "Maximal_strength"
    RELATIVE_STRENGTH = "Relative_strength"
    EXPLOSIVE_STRENGTH = "Explosive_strength"
    STRENGTH_ENDURANCE = "Strength_endurance"
    AGILE_STRENGTH = "Agile_strength"
    SPEED_STRENGTH = "Speed_strength"
    STARTING_STRENGTH = "Starting_strength"


class ConditioningDimension(str, Enum):
    CARDIOVASCULAR_ENDURANCE = "cardiovascular_endurance"
    MUSCLE_STRENGTH = "Muscle_strength"
    MUSCLE_ENDURANCE = "Muscle_endurance"
    FLEXIBILITY = "Flexibility"
    BODY_COMPOSITION = "Body_composition"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ReadinessScore(BaseModel):
    user_id: int
    readiness_score: int
    contributing_factors: str
    readiness_date: date
    source: Source = Source.AUTO
    alignment_score: float = 0.0
    overtraining_score: float = 0.0


class UserGoal(BaseModel):
    user_id: int
    goal_type: GoalType
    description: str
    target_date: date


class DailyCheckIn(BaseModel):
    weight: int
    sleep: int
    stress: int
    energy: int
    soreness: int

    @field_validator("weight")
    def validate_weight(cls, v):
        if not isinstance(v, int):
            raise ValueError("Weight must be an integer")
        if v < 0:
            raise ValueError("Weight must be greater than 0")
        return v

    @field_validator("sleep")
    def validate_sleep(cls, v):
        if v < 1 or v > 10:
            raise ValueError("Sleep must be between 1 and 10")
        return v

    @field_validator("stress")
    def validate_stress(cls, v):
        if v < 1 or v > 10:
            raise ValueError("Stress must be between 1 and 10")
        return v

    @field_validator("energy")
    def validate_energy(cls, v):
        if v < 1 or v > 10:
            raise ValueError("Energy must be between 1 and 10")
        return v

    @field_validator("soreness")
    def validate_soreness(cls, v):
        if v < 1 or v > 10:
            raise ValueError("Soreness must be between 1 and 10")
        return v


class UserRegistration(BaseModel):
    email: EmailStr
    password: str
    name: str
    gender: Gender
    dob: date
    height: float
    weight: float
    initialActivityLevel: ActivityLevel
    goal: GoalType

    @field_validator("password")
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password too short")
        if not re.search(r"[a-zA-Z]", v):
            raise ValueError("Password must contain at least one letter")

            # Check for at least one digit
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")

            # Check for at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")

        return v

    @field_validator("height")
    def validate_height(cls, v):
        if v <= 0:
            raise ValueError("Height must be positive")
        return v

    @field_validator("weight")
    def validate_weight(cls, v):
        if v <= 0:
            raise ValueError("Weight must be positive")
        return v
