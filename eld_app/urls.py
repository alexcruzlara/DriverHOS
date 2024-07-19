from django.urls import re_path
from .views import TruckListView, DriversListView, DriverView, TrucksHOSViolationsView, DrivingScheduleView, \
    DrivingScheduleWithViolations

urlpatterns = [
    re_path(r'^trucks/?$', TruckListView.as_view(), name='truck-list'),
    #re_path(r'^drivers/?$', DriversListView.as_view(), name='drivers-list'),
    #re_path(r'^driver/(?P<id>\w+)/?$', DriverView.as_view(), name='driver'),
    #re_path(r'^drivers/violations/(?P<id>\w+)/?$', TrucksHOSViolationsView.as_view(), name='trucks-violations'),
    #re_path(r'^drivers/schedule/(?P<id>\w+)/?$', DrivingScheduleView.as_view(), name='driving-schedule'),
    re_path(r'^drivers/hos/(?P<id>\w+)/?$', DrivingScheduleWithViolations.as_view(), name='driving-schedule'),
]