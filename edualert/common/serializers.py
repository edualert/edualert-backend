import io

from django.utils.translation import gettext as _
from rest_framework import serializers

from edualert.common.validators import FileNameValidator


class CsvUploadSerializer(serializers.Serializer):
    file = serializers.FileField(max_length=100, allow_empty_file=False)

    def validate(self, attrs):
        file = attrs['file']

        FileNameValidator(file.name)

        extension = file.name.split('.')[1]
        if extension != 'csv':
            raise serializers.ValidationError({'file': _('File must be csv.')})

        # Decode the file
        if file.multiple_chunks():
            data = ''
            for chunk in file.chunks():
                data += chunk
        else:
            data = file.read()

        try:
            file = data.decode('utf-8')
        except UnicodeDecodeError:
            raise serializers.ValidationError({'file': _('Invalid file encoding.')})

        # Replace it with an in memory file object
        attrs['file'] = io.StringIO(file)

        return attrs

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass
