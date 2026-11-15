from django.db.models import Q
import django_filters
from .models import AdmissionSession, CourseAllocation, Course


class AdmissionSessionFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr="icontains", label="")

    class Meta:
        model = AdmissionSession
        fields = ["title"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Change html classes and placeholders
        self.filters["title"].field.widget.attrs.update(
            {"class": "au-input", "placeholder": "admission session"}
        )


class CourseAllocationFilter(django_filters.FilterSet):
    teacher = django_filters.CharFilter(method="filter_by_teacher", label="")
    course = django_filters.filters.CharFilter(method="filter_by_course", label="")

    class Meta:
        model = CourseAllocation
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Change html classes and placeholders
        self.filters["teacher"].field.widget.attrs.update(
            {"class": "au-input", "placeholder": "teacher"}
        )
        self.filters["course"].field.widget.attrs.update(
            {"class": "au-input", "placeholder": "Course"}
        )

    def filter_by_teacher(self, queryset, name, value):
        return queryset.filter(
            Q(teacher__first_name__icontains=value)
            | Q(teacher__last_name__icontains=value)
        )

    def filter_by_course(self, queryset, name, value):
        return queryset.filter(courses__title__icontains=value)
