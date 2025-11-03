from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from telegram.permissions import IsTelegramAdminIfProvided

from decidim.client.api_client import ApiClient
from decidim.services.assemblies import AssembliesService
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes


class AdminAssembliesList(APIView):
    permission_classes = [IsAuthenticated & IsTelegramAdminIfProvided]

    @extend_schema(
        summary="List Assemblies (Admin)",
        description="Retrieve a list of assemblies with optional title search, pagination, and sorting.",
        parameters=[
            OpenApiParameter(
                name="title",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Search term to filter assemblies by title.",
            ),
            OpenApiParameter(
                name="page",
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Page number for pagination.",
            ),
            OpenApiParameter(
                name="sort",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Sorting criteria.",
            ),
        ],
        responses={200: OpenApiTypes.OBJECT},  # troque por um Serializer se tiver
    )
    def get(self, request):
        api = ApiClient()
        svc = AssembliesService(api)

        title = request.query_params.get("title")
        page = int(request.query_params.get("page", "1"))
        sort = request.query_params.get("sort")

        if title:
            data = svc.search_title(title, page=page, sort=sort)
        else:
            data = svc.list(page=page, sort=sort)

        return Response(data, 200)
