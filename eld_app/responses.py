"""
Responses holds the dataclasses for the responses that the API will return.
"""
from dataclasses import field
from datetime import timedelta, datetime
from typing import List, Dict, Any, Optional

from pydantic import BaseModel
from pydantic.dataclasses import dataclass


@dataclass
class TruckHOSViolations:
    truck_id: str
    violations: int
    violations_data: list[dict[str, str]]


@dataclass
class DrivingSegment:
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    segment_type: Optional[str] = None

    def to_dict(self):
        return {
            "start": self.start.isoformat() if self.start else None,
            "end": self.end.isoformat() if self.end else None,
            "segment_type": self.segment_type
        }


@dataclass
class DrivingSchedules:
    driver_id: str
    pickup_time: datetime
    dropoff_time: datetime
    driving_segments: List[DrivingSegment] = field(default_factory=list)
    rest_periods: List[DrivingSegment] = field(default_factory=list)
