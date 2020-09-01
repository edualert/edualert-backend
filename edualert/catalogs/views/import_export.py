import csv

from django.http import HttpResponse, Http404
from django.utils import timezone
from rest_framework.generics import get_object_or_404
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from edualert.academic_calendars.utils import get_current_academic_calendar
from edualert.catalogs.models import StudentCatalogPerSubject
from edualert.catalogs.utils import CatalogsImporter, get_catalog_csv_representation
from edualert.common.permissions import IsTeacher
from edualert.common.serializers import CsvUploadSerializer
from edualert.study_classes.models import StudyClass
from edualert.subjects.models import Subject


class ExportSubjectCatalogs(APIView):
    permission_classes = (IsTeacher,)

    def get(self, request, *args, **kwargs):
        profile = self.request.user.user_profile
        today = timezone.now()

        study_class = get_object_or_404(StudyClass, id=self.kwargs['study_class_id'])
        subject = get_object_or_404(
            Subject.objects.distinct(),
            id=self.kwargs['subject_id'],
            teacher_class_through__study_class=study_class,
            teacher_class_through__teacher=profile
        )

        file_name = f"raport_{study_class.class_grade}_{study_class.class_letter}_{subject.id}_{today.minute}_{today.second}.csv"
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'

        # Don't set the field names here
        writer = csv.DictWriter(response, [], restval='-')
        wrote_header = False

        catalogs = StudentCatalogPerSubject.objects.filter(
            study_class=study_class,
            subject=subject
        ).prefetch_related(
            'student__labels',
            'examination_grades',
            'grades',
            'absences'
        ).order_by(
            'student__full_name'
        )

        for catalog in catalogs:
            fields = get_catalog_csv_representation(catalog, study_class)

            # Only write the headers once per file
            if not wrote_header:
                writer.fieldnames = fields.keys()
                writer.writeheader()
                wrote_header = True

            # Remove keys which don't have a value, and handle Boolean translation
            cleaned_fields = {}
            for key, value in fields.items():
                if value is True:
                    cleaned_fields[key] = 'Da'
                elif value is False:
                    cleaned_fields[key] = 'Nu'
                elif value:
                    cleaned_fields[key] = value
                else:
                    cleaned_fields[key] = '-'

            writer.writerow(cleaned_fields)

        return response


class ImportSubjectCatalogs(APIView):
    permission_classes = (IsTeacher,)
    parser_class = (MultiPartParser,)

    def post(self, request, *args, **kwargs):
        profile = self.request.user.user_profile
        current_calendar = get_current_academic_calendar()

        if not current_calendar:
            raise Http404()

        study_class = get_object_or_404(
            StudyClass,
            id=self.kwargs['study_class_id'],
            academic_year=current_calendar.academic_year
        )
        subject = get_object_or_404(
            Subject.objects.distinct(),
            id=self.kwargs['subject_id'],
            teacher_class_through__study_class=study_class,
            teacher_class_through__teacher=profile,
        )

        serializer = CsvUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file = serializer.validated_data['file']
        importer = CatalogsImporter(file=file, study_class=study_class, subject=subject, current_calendar=current_calendar)

        return Response(
            data=importer.import_catalogs_and_get_report()
        )
