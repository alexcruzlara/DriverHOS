from django.db import models

# Create your models here.
from pydantic import BaseModel
from typing import List, Optional

from pydantic.fields import Field


class DriverHosInformation(BaseModel):
    driver_id: Optional[str] = Field(None, alias='driverId')
    truck_name: Optional[str] = Field(None, alias='truckName')
    duty_status: Optional[str] = Field(None, alias='dutyStatus')
    duty_status_start_time: Optional[str] = Field(None, alias='dutyStatusStartTime')
    shift_work_minutes: Optional[float] = Field(None, alias='shiftWorkMinutes')
    shift_drive_minutes: Optional[float] = Field(None, alias='shiftDriveMinutes')
    cycle_work_minutes: Optional[float] = Field(None, alias='cycleWorkMinutes')
    max_shift_work_minutes: Optional[int] = Field(None, alias='maxShiftWorkMinutes')
    max_shift_drive_minutes: Optional[int] = Field(None, alias='maxShiftDriveMinutes')
    max_cycle_work_minutes: Optional[int] = Field(None, alias='maxCycleWorkMinutes')
    home_terminal_time_zone_windows: Optional[str] = Field(None, alias='homeTerminalTimeZoneWindows')
    home_terminal_time_zone_iana: Optional[str] = Field(None, alias='homeTerminalTimeZoneIana')

    class Config:
        allow_population_by_field_name = True


class DriverDutyStatus(BaseModel):
    startTime: str
    dutyStatus: Optional[str]
    location: Optional[str]


class DriverDutyStatusDtoListResult(BaseModel):
    list: Optional[List[DriverDutyStatus]]
    hasMore: bool
    lastTimestamp: Optional[str]


class TruckLocation(BaseModel):
    name: Optional[str]
    location: Optional[str] = Field(default=None)
    lat: Optional[float]
    lng: Optional[float]
    speed: Optional[int] = Field(default=None)
    timeStamp: Optional[str]
