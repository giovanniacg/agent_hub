from api.views import AdminAssembliesList
from django.urls import path


urlpatterns = [
    path("admin/assemblies/", AdminAssembliesList.as_view(), name="admin-assemblies"),
]
