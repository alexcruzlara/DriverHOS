from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from eld_app.models import DriverHosInformation
from eld_app.utils import get_truck_eld_data, get_drivers_data, get_driver_data, detect_violation, parse_and_verify_utc, \
    plan_driving_schedule


# Create your views here.

class TruckListView(APIView):

    def get(self, request):
        trucks = get_truck_eld_data()
        return Response(trucks, status=status.HTTP_200_OK)


class DriversListView(APIView):
    def get(self, request):
        drivers = get_drivers_data()
        return Response(drivers, status=status.HTTP_200_OK)


class DriverView(APIView):
    def get(self, request, *args, **kwargs):
        driver_id = kwargs.get('id')
        if driver_id is None:
            return Response({"error": "Driver ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        drivers = get_driver_data(id=driver_id)
        return Response(drivers, status=status.HTTP_200_OK)


class TrucksHOSViolationsView(APIView):
    def get(self, request, *args, **kwargs):
        driver_id = kwargs.get('id')
        if driver_id is None:
            return Response({"error": "Driver ID is required"}, status=status.HTTP_400_BAD_REQUEST)
        drivers = get_drivers_data()
        driver = next((item for item in drivers if item['driverId'] == driver_id), None)
        driver = DriverHosInformation(**driver)
        result = detect_violation(driver)
        return Response(result.__dict__, status=status.HTTP_200_OK)


class DrivingScheduleView(APIView):
    def post(self, request, *args, **kwargs):
        driver_id = kwargs.get('id')
        if driver_id is None:
            return Response({"error": "Driver ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        body_data = request.data
        start = body_data.get('start')
        end = body_data.get('end')

        if not start or not end:
            return Response({"error": "Start and end dates are required"}, status=status.HTTP_400_BAD_REQUEST)

        start_date = parse_and_verify_utc(start)
        end_date = parse_and_verify_utc(end)

        if not start_date or not end_date:
            return Response({"error": "Invalid or non-UTC dates provided"}, status=status.HTTP_400_BAD_REQUEST)

        drivers = get_drivers_data()
        driver = next((item for item in drivers if item['driverId'] == driver_id), None)
        driver = DriverHosInformation(**driver)

        result = plan_driving_schedule(start_date, end_date, driver)
        return Response(result, status=status.HTTP_200_OK)


class DrivingScheduleWithViolations(APIView):
    def post(self, request, *args, **kwargs):
        driver_id = kwargs.get('id')
        if driver_id is None:
            return Response({"error": "Driver ID is required"}, status=status.HTTP_400_BAD_REQUEST)

        body_data = request.data
        start = body_data.get('start')
        end = body_data.get('end')

        if not start or not end:
            return Response({"error": "Start and end dates are required"}, status=status.HTTP_400_BAD_REQUEST)

        start_date = parse_and_verify_utc(start)
        end_date = parse_and_verify_utc(end)

        if not start_date or not end_date:
            return Response({"error": "Invalid or non-UTC dates provided"}, status=status.HTTP_400_BAD_REQUEST)

        drivers = get_drivers_data()
        driver = next((item for item in drivers if item['driverId'] == driver_id), None)
        if driver is None:
            return Response({"error": "Driver not found"}, status=status.HTTP_404_NOT_FOUND)

        driver = DriverHosInformation(**driver)

        if driver.duty_status == "OFF":
            return Response({
                "violations": [
                    {
                        "violation": "No violation due to driver being off duty",
                    }
                ]
            })

        if driver.duty_status == "SB":
            return Response({
                "violations": [
                    {
                        "violation": "No violation due to driver being in the sleeper berth",
                    }
                ]
            })

        if driver.duty_status == "PC":
            return Response({
                "violations": [
                    {
                        "violation": "No violation due to driver being in the personal conveyance",
                    }
                ]
            })

        if driver.duty_status == "YM":
            return Response({
                "violations": [
                    {
                        "violation": "No violation due to driver being in the yard move",
                    }
                ]
            })

        violations = detect_violation(driver)
        schedule = plan_driving_schedule(start_date, end_date, driver)

        return Response({"violations": violations.__dict__["violations_data"], "suggested_schedule": schedule}, status=status.HTTP_200_OK)
