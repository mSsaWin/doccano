import json
import re

from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, status
from rest_framework.exceptions import ParseError
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import LabelValidationError
from .models import CategoryType, LabelType, RelationType, SpanType
from .serializers import (
    CategoryTypeSerializer,
    LabelSerializer,
    RelationTypeSerializer,
    SpanTypeSerializer,
)
from projects.models import Project
from projects.permissions import (
    IsProjectAdmin,
    IsProjectMember,
    IsProjectStaffAndReadOnly,
)


def camel_to_snake(name):
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", name).lower()


def camel_to_snake_dict(d):
    return {camel_to_snake(k): v for k, v in d.items()}


class LabelPagination(LimitOffsetPagination):
    default_limit = 50
    max_limit = 1000


class LabelList(generics.ListCreateAPIView):
    model = LabelType
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    serializer_class = LabelSerializer
    pagination_class = LabelPagination
    search_fields = ['text']
    ordering_fields = ['created_at', 'text', 'usage_count']
    ordering = ['-usage_count', 'text']

    def get_permissions(self):
        project = get_object_or_404(Project, pk=self.kwargs["project_id"])
        # Allow all project members to read labels (GET)
        if self.request.method in ["GET", "HEAD", "OPTIONS"]:
            self.permission_classes = [IsAuthenticated & IsProjectMember]
        # Allow creating labels if project allows it
        elif project.allow_member_to_create_label_type and self.request.method == "POST":
            self.permission_classes = [IsAuthenticated & IsProjectMember]
        # Only admins can modify/delete
        else:
            self.permission_classes = [IsAuthenticated & IsProjectAdmin]
        return super().get_permissions()

    def get_queryset(self):
        queryset = self.model.objects.filter(project=self.kwargs["project_id"])
        
        # Add usage count annotation based on label type
        if self.model.__name__ == 'CategoryType':
            queryset = queryset.annotate(usage_count=Count('category'))
        elif self.model.__name__ == 'SpanType':
            queryset = queryset.annotate(usage_count=Count('span'))
        elif self.model.__name__ == 'RelationType':
            queryset = queryset.annotate(usage_count=Count('relation'))
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        # Support disabling pagination with ?limit=none or ?no_page=true
        if request.query_params.get('limit') == 'none' or request.query_params.get('no_page') == 'true':
            self.pagination_class = None
        return super().list(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(project_id=self.kwargs["project_id"])

    def delete(self, request, *args, **kwargs):
        delete_ids = request.data["ids"]
        self.model.objects.filter(pk__in=delete_ids).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CategoryTypeList(LabelList):
    model = CategoryType
    serializer_class = CategoryTypeSerializer


class CategoryTypeDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = CategoryType.objects.all()
    serializer_class = CategoryTypeSerializer
    lookup_url_kwarg = "label_id"
    permission_classes = [IsAuthenticated & IsProjectMember]


class SpanTypeList(LabelList):
    model = SpanType
    serializer_class = SpanTypeSerializer


class SpanTypeDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = SpanType.objects.all()
    serializer_class = SpanTypeSerializer
    lookup_url_kwarg = "label_id"
    permission_classes = [IsAuthenticated & IsProjectMember]


class RelationTypeList(LabelList):
    model = RelationType
    serializer_class = RelationTypeSerializer


class RelationTypeDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = RelationType.objects.all()
    serializer_class = RelationTypeSerializer
    lookup_url_kwarg = "label_id"
    permission_classes = [IsAuthenticated & IsProjectMember]


class LabelUploadAPI(APIView):
    parser_classes = (MultiPartParser,)
    permission_classes = [IsAuthenticated & IsProjectAdmin]
    serializer_class = LabelSerializer

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        if "file" not in request.data:
            raise ParseError("Empty content")
        try:
            labels = json.load(request.data["file"])
            labels = list(map(camel_to_snake_dict, labels))
            serializer = self.serializer_class(data=labels, many=True)
            serializer.is_valid(raise_exception=True)
            serializer.save(project_id=kwargs["project_id"])
            return Response(status=status.HTTP_201_CREATED)
        except json.decoder.JSONDecodeError:
            raise ParseError("The file format is invalid.")
        except IntegrityError:
            raise LabelValidationError


class CategoryTypeUploadAPI(LabelUploadAPI):
    serializer_class = CategoryTypeSerializer


class SpanTypeUploadAPI(LabelUploadAPI):
    serializer_class = SpanTypeSerializer


class RelationTypeUploadAPI(LabelUploadAPI):
    serializer_class = RelationTypeSerializer


class PopularLabelsMixin:
    """Mixin to get popular labels (most frequently used)"""
    
    def get_popular_queryset(self, queryset, limit=50):
        # Add usage count annotation
        if self.model.__name__ == 'CategoryType':
            queryset = queryset.annotate(usage_count=Count('category'))
        elif self.model.__name__ == 'SpanType':
            queryset = queryset.annotate(usage_count=Count('span'))
        elif self.model.__name__ == 'RelationType':
            queryset = queryset.annotate(usage_count=Count('relation'))
        
        # Return most used labels
        return queryset.filter(usage_count__gt=0).order_by('-usage_count', 'text')[:limit]


class CategoryTypePopular(PopularLabelsMixin, generics.ListAPIView):
    model = CategoryType
    serializer_class = CategoryTypeSerializer
    permission_classes = [IsAuthenticated & IsProjectMember]
    pagination_class = None
    
    def get_queryset(self):
        queryset = self.model.objects.filter(project=self.kwargs["project_id"])
        limit = int(self.request.query_params.get('limit', 50))
        popular = self.get_popular_queryset(queryset, limit)
        
        # If no popular labels (no usage yet), return first N labels instead
        if not popular.exists():
            return queryset.order_by('created_at')[:limit]
        return popular


class SpanTypePopular(PopularLabelsMixin, generics.ListAPIView):
    model = SpanType
    serializer_class = SpanTypeSerializer
    permission_classes = [IsAuthenticated & IsProjectMember]
    pagination_class = None
    
    def get_queryset(self):
        queryset = self.model.objects.filter(project=self.kwargs["project_id"])
        limit = int(self.request.query_params.get('limit', 50))
        popular = self.get_popular_queryset(queryset, limit)
        
        # If no popular labels (no usage yet), return first N labels instead
        if not popular.exists():
            return queryset.order_by('created_at')[:limit]
        return popular


class RelationTypePopular(PopularLabelsMixin, generics.ListAPIView):
    model = RelationType
    serializer_class = RelationTypeSerializer
    permission_classes = [IsAuthenticated & IsProjectMember]
    pagination_class = None
    
    def get_queryset(self):
        queryset = self.model.objects.filter(project=self.kwargs["project_id"])
        limit = int(self.request.query_params.get('limit', 50))
        popular = self.get_popular_queryset(queryset, limit)
        
        # If no popular labels (no usage yet), return first N labels instead
        if not popular.exists():
            return queryset.order_by('created_at')[:limit]
        return popular
