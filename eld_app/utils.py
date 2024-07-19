import json
import os

import requests

from eld_app.models import TruckLocation, DriverHosInformation
from eld_app.responses import TruckHOSViolations, DrivingSchedules, DrivingSegment
from datetime import timedelta, datetime, timezone

from dateutil import parser

PROLOGS_API_BASE_URL = "https://publicapi-stage.prologs.us/api/v1"

PROLOGS_API_CONNECT_BASE_URL = "https://identity-stage.prologs.us/connect/token"


def get_access_token(client_id, client_secret):
    url = PROLOGS_API_CONNECT_BASE_URL
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    }

    try:
        response = requests.post(url, headers=headers, data=data)
        # response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes

        result = response.json()  # .get('access_token')
        return result["access_token"]

    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None


def get_truck_eld_data() -> list[TruckLocation]:
    client_id, client_secret = os.getenv('PROLOGS_CLIENT_ID'), os.getenv('PROLOGS_API_KEY')
    url = f"{PROLOGS_API_BASE_URL}/trucks/"

    access_token = get_access_token(client_id, client_secret)

    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    response = requests.get(url, headers=headers).json()

    return response


def get_drivers_data() -> list[DriverHosInformation]:
    client_id, client_secret = os.getenv('PROLOGS_CLIENT_ID'), os.getenv('PROLOGS_API_KEY')
    url = f"{PROLOGS_API_BASE_URL}/drivers/"

    access_token = get_access_token(client_id, client_secret)

    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    response = requests.get(url, headers=headers).json()

    return response


def get_driver_data(id: str) -> list[DriverHosInformation]:
    client_id, client_secret = os.getenv('PROLOGS_CLIENT_ID'), os.getenv('PROLOGS_API_KEY')
    url = f"{PROLOGS_API_BASE_URL}/drivers/{id}"

    access_token = get_access_token(client_id, client_secret)

    print(access_token)

    headers = {
        'Authorization': f'Bearer {access_token}'
    }

    response = requests.get(url, headers=headers).json()

    return response


def detect_violation(driver_data: DriverHosInformation) -> TruckHOSViolations:
    # To understand the logic of the violations, you can check to the following link:
    # https://www.fmcsa.dot.gov/regulations/hours-service/summary-hours-service-regulations

    violations = []

    # Check for 11-Hour Driving Limit Violation
    if driver_data.shift_drive_minutes > 11 * 60:
        violations.append({
            'violation': '11-Hour Driving Limit',
            'details': f'Drove {driver_data.shift_drive_minutes} minutes, exceeding the 660 minutes limit.'
        })

    # Check for 14-Hour Limit Violation
    if driver_data.shift_work_minutes > 14 * 60:
        violations.append({
            'violation': '14-Hour Limit',
            'details': f'Worked {driver_data.shift_work_minutes} minutes, exceeding the 840 minutes limit.'
        })

    # Check for 70-Hour Limit Violation
    if driver_data.cycle_work_minutes > 70 * 60:
        violations.append({
            'violation': '70-Hour Limit',
            'details': f'Worked {driver_data.cycle_work_minutes} minutes in the cycle, exceeding the 4200 minutes limit.'
        })

    return TruckHOSViolations(
        truck_id=driver_data.driver_id,
        violations=len(violations),
        violations_data=violations
    )


def plan_driving_schedule(pickup: datetime, dropoff: datetime,
                          driver: DriverHosInformation):
    # Constants
    MAX_SHIFT_WORK_MINUTES = 840  # 14 hours
    MAX_SHIFT_DRIVE_MINUTES = 660  # 11 hours
    MAX_CYCLE_WORK_MINUTES = 4200  # 70 hours in 8 days

    DRIVE_4_HOURS = timedelta(hours=4)

    REST_30_MINUTES = timedelta(minutes=30)
    REST_2_HOURS = timedelta(hours=2)
    REST_7_HOURS = timedelta(hours=7)
    REST_34_HOURS = timedelta(hours=34)

    def pause_when_reach_dropoff_time(current_time, dropoff_time, duration):
        if current_time - dropoff_time >= timedelta(minutes=duration) or (
                current_time + timedelta(minutes=duration)) > dropoff_time:
            return True
        return False


    shift_work_minutes = driver.shift_work_minutes
    shift_drive_minutes = driver.shift_drive_minutes
    cycle_work_minutes = driver.cycle_work_minutes

    driving_segments = []
    rest_periods = []

    current_time = pickup
    driving_minutes = 0

    while current_time < dropoff:
        if dropoff == current_time:
            break

        if cycle_work_minutes >= MAX_CYCLE_WORK_MINUTES:
            if pause_when_reach_dropoff_time(current_time, dropoff, 34 * 60):
                rest_start = current_time
                rest_periods.append({
                    "start": rest_start.isoformat(),
                    "end": dropoff.isoformat(),
                    "segment_type": "34-Hour Reset",
                    "duration": abs((rest_start - dropoff).total_seconds() / 60)
                })
                current_time = dropoff

                continue

            rest_start = current_time
            rest_end = rest_start + REST_34_HOURS
            rest_periods.append({
                "start": rest_start.isoformat(),
                "end": rest_end.isoformat(),
                "segment_type": "34-Hour Reset",
                "duration": 34 * 60
            })
            cycle_work_minutes = 0
            shift_drive_minutes = 0
            driving_minutes = 0

            current_time = rest_end

            continue

        drive_time = dropoff - current_time

        if MAX_SHIFT_DRIVE_MINUTES <= (shift_drive_minutes + driving_minutes):
            # DRIVER HAS REACHED THE MAXIMUM DRIVING TIME
            # Rest for 7h

            if pause_when_reach_dropoff_time(current_time, dropoff, 7 * 60):
                rest_start = current_time
                rest_periods.append({
                    "start": rest_start.isoformat(),
                    "end": dropoff.isoformat(),
                    "segment_type": "7-Hour Break",
                    "duration": abs((rest_start - dropoff).total_seconds() / 60)
                })
                current_time = dropoff

                continue

            rest_start = current_time
            rest_end = rest_start + REST_7_HOURS

            rest_periods.append({
                "start": rest_start.isoformat(),
                "end": rest_end.isoformat(),
                "segment_type": "7-Hour Break",
                "duration": 420
            })

            shift_drive_minutes = 0
            cycle_work_minutes = cycle_work_minutes + 420
            driving_minutes = 0

            current_time = rest_end

            continue

        if MAX_SHIFT_DRIVE_MINUTES / 2 >= driving_minutes > 0:

            if pause_when_reach_dropoff_time(current_time, dropoff, 240):
                drive_start = current_time
                driving_segments.append({
                    "start": drive_start.isoformat(),
                    "end": dropoff.isoformat(),
                    "segment_type": "Driving",
                    "duration": abs((drive_start - dropoff).total_seconds() / 60)
                })
                current_time = dropoff

                continue

            # SPLIT DRIVES TIMES TO GIVE DRIVER A REST
            drive_start = current_time
            drive_time = timedelta(minutes=MAX_SHIFT_DRIVE_MINUTES / 2)
            drive_end = drive_start + drive_time

            driving_segments.append({
                "start": drive_start.isoformat(),
                "end": drive_end.isoformat(),
                "segment_type": "Driving",
                "duration": drive_time.total_seconds() / 60
            })

            driving_minutes = driving_minutes + MAX_SHIFT_DRIVE_MINUTES / 2

            if pause_when_reach_dropoff_time(current_time, dropoff, 2 * 60):
                rest_start = current_time
                rest_periods.append({
                    "start": rest_start.isoformat(),
                    "end": dropoff.isoformat(),
                    "segment_type": "2-Hour Break",
                    "duration": 120
                })
                current_time = dropoff

                continue

            # Rest for 2h
            rest_start = drive_end
            rest_end = rest_start + REST_2_HOURS

            rest_periods.append({
                "start": rest_start.isoformat(),
                "end": rest_end.isoformat(),
                "segment_type": "2-Hour Break",
                "duration": 120
            })

            current_time = rest_end

            shift_drive_minutes = shift_drive_minutes + driving_minutes
            cycle_work_minutes = cycle_work_minutes + driving_minutes + 120

            continue

        if pause_when_reach_dropoff_time(current_time, dropoff, 240):  # pause when reach dropoff time
            drive_start = current_time
            driving_segments.append({
                "start": drive_start.isoformat(),
                "end": dropoff.isoformat(),
                "segment_type": "Driving",
                "duration": abs((drive_start - dropoff).total_seconds() / 60)
            })
            current_time = dropoff
            continue

        if shift_drive_minutes + 240 >= MAX_SHIFT_DRIVE_MINUTES:
            # DRIVER HAS REACHED THE MAXIMUM DRIVING TIME
            drive_start = current_time
            drive_end = current_time + (
                    timedelta(minutes=MAX_SHIFT_DRIVE_MINUTES) - timedelta(minutes=shift_drive_minutes))
            driving_segments.append({
                "start": drive_start.isoformat(),
                "end": drive_end.isoformat(),
                "segment_type": "Driving",
                "duration": (drive_end - drive_start).total_seconds() / 60
            })

            driving_minutes = (drive_end - drive_start).total_seconds() / 60

            shift_drive_minutes = shift_drive_minutes + driving_minutes
            cycle_work_minutes = cycle_work_minutes + driving_minutes

            current_time = drive_end

            continue

            # Drive for 4 hours
        drive_start = current_time
        drive_end = current_time + DRIVE_4_HOURS
        driving_segments.append({
            "start": drive_start.isoformat(),
            "end": drive_end.isoformat(),
            "segment_type": "Driving",
            "duration": 240
        })

        driving_minutes = driving_minutes + 240

        # Rest for 30 minutes
        rest_start = drive_end
        rest_end = rest_start + REST_30_MINUTES
        rest_periods.append({
            "start": rest_start.isoformat(),
            "end": rest_end.isoformat(),
            "segment_type": "30-Minute Break",
            "duration": 30
        })

        current_time = rest_end

        shift_drive_minutes = shift_drive_minutes + driving_minutes
        cycle_work_minutes = cycle_work_minutes + driving_minutes + 30

        continue

    timeline = driving_segments + rest_periods
    timeline.sort(key=lambda x: datetime.fromisoformat(x["start"]))

    return {
        "timeline": timeline,
        "driving_segments": driving_segments,
        "rest_periods": rest_periods,
    }


def parse_and_verify_utc(date_str):
    try:
        parsed_date = parser.isoparse(date_str)
        if parsed_date.tzinfo is not None and parsed_date.tzinfo.utcoffset(
                parsed_date) == timezone.utc.utcoffset(
            parsed_date):
            return parsed_date
        else:
            return None
    except ValueError:
        return None
