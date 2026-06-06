from django.contrib import admin
from django.urls import path, include # include અહિયાં ઉમેર્યું છે

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')), # આપણી એપ્લિકેશનની બધી લિંક્સ અહિયાં કનેક્ટ કરી દીધી
]