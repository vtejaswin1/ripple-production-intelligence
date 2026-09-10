from datetime import date, datetime
from pydantic import BaseModel, Field


class AvailabilityWindow(BaseModel):
    available_date: date
    available_from: datetime
    available_to: datetime


class ActorManifest(BaseModel):
    actor_name: str
    character_name: str

    availability: list[AvailabilityWindow] = Field(
        default_factory=list
    )


class LocationConstraintManifest(BaseModel):
    constraint_type: str
    constraint_description: str
    effective_date: date


class LocationManifest(BaseModel):
    location_name: str
    location_type: str
    city: str = ""

    supports_day_shoot: bool = True
    supports_night_shoot: bool = True

    base_cost_per_hour: float = 0

    availability: list[AvailabilityWindow] = Field(
        default_factory=list
    )

    constraints: list[LocationConstraintManifest] = Field(
        default_factory=list
    )


class SceneScheduleManifest(BaseModel):
    scene_number: int

    title: str = ""
    

    scheduled_date: date
    scheduled_start_time: datetime

    estimated_duration_minutes: int
    estimated_cost: float = 0

    location_name: str
    time_of_day: str = "UNKNOWN"

    characters: list[str] = Field(
        default_factory=list
    )


class ProductionManifest(BaseModel):
    actors: list[ActorManifest] = Field(
        default_factory=list
    )

    locations: list[LocationManifest] = Field(
        default_factory=list
    )

    scenes: list[SceneScheduleManifest] = Field(
        default_factory=list
    )