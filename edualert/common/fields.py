from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import gettext_lazy as _
from rest_framework.fields import Field


class PrimaryKeyRelatedField(Field):
    default_error_messages = {
        'required': _('This field is required.'),
        'does_not_exist': _('Invalid pk "{pk_value}" - object does not exist.'),
        'incorrect_type': _('Incorrect type. Expected pk value, received {data_type}.'),
    }

    def __init__(self, queryset, *args, many=False, **kwargs):
        self.queryset = queryset
        self.many = many
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        try:
            if self.many:
                queryset = self.queryset.filter(pk__in=data).all()
                found_ids = [instance.pk for instance in queryset]
                for missing_pk in set(data) - set(found_ids):
                    self.fail('does_not_exist', pk_value=missing_pk)
                return queryset

            return self.queryset.get(pk=data)
        except ObjectDoesNotExist:
            self.fail('does_not_exist', pk_value=data)
        except (TypeError, ValueError):
            self.fail('incorrect_type', data_type=type(data).__name__)

    def to_representation(self, value):
        if self.many:
            return value.values_list('pk', flat=True)
        return value.pk
