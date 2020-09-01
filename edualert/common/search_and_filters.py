from django.db.models.constants import LOOKUP_SEP
from rest_framework import filters


class CommonSearchFilter(filters.SearchFilter):
    def construct_search(self, field_name):
        lookup = self.lookup_prefixes.get(field_name[0])
        if lookup:
            field_name = field_name[1:]
        else:
            lookup = LOOKUP_SEP.join(['unaccent', 'icontains'])
        return LOOKUP_SEP.join([field_name, lookup])


class CommonOrderingFilter(filters.OrderingFilter):
    ordering_fields_aliases = {}
    ordering_extra_annotations = {}

    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view)[0]
        ordering_fields_aliases = getattr(view, 'ordering_fields_aliases', self.ordering_fields_aliases)
        ordering_extra_annotations = getattr(view, 'ordering_extra_annotations', self.ordering_extra_annotations)

        default_ordering = self.get_default_ordering(view)
        for order_by in default_ordering:
            annotation = ordering_extra_annotations.get(order_by)
            if annotation:
                queryset = queryset.annotate(**{order_by: annotation})

        if ordering:
            reverse = False
            if ordering.startswith('-'):
                reverse = True
                ordering = ordering.replace('-', '', 1)

            annotation = ordering_extra_annotations.get(ordering)
            if annotation:
                queryset = queryset.annotate(**{ordering: annotation})

            order_param = ordering_fields_aliases.get(ordering) or ordering

            if reverse:
                order_param = '-' + order_param

            return queryset.order_by(order_param, *default_ordering)

        return queryset.order_by(*default_ordering)
