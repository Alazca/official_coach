from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional

class Gender(Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

class ActivityLevel(Enum):
    SEDENTARY = "sedentary"
    LIGHTLY_ACTIVE = "lightly_active"
    MODERATELY_ACTIVE = "moderately_active"
    VERY_ACTIVE = "very_active"
    EXTREMELY_ACTIVE = "extremely_active"

@dataclass
class UserRegistration:
    email: str
    password: str
    name: str
    gender: Gender
    dob: date
    height: float
    weight: float
    initialActivityLevel: ActivityLevel

@dataclass
class DailyCheckIn:
    weight: float
    sleep: int
    stress: int
    energy: int
    soreness: int