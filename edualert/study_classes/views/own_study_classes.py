from rest_framework.response import Response
from rest_framework import views, generics

from edualert.common.permissions import IsTeacher
from edualert.study_classes.serializers import TeacherClassThroughOwnStudyClassSerializer, OwnStudyClassSerializer
from edualert.study_classes.constants import CLASS_GRADE_MAPPING


class OwnStudyClassList(views.APIView):
    permission_classes = (IsTeacher,)

    def get(self, *args, **kwargs):
        response = {"class_master": []}
        profile = self.request.user.user_profile
        taught_classes = profile.teacher_class_through.filter(
            academic_year=self.kwargs['academic_year']
        ).select_related(
            'study_class'
        ).distinct('study_class')

        for taught_class in taught_classes:
            class_data = TeacherClassThroughOwnStudyClassSerializer(
                instance=taught_class,
                context={
                    'user_profile': profile,
                    'academic_year': self.kwargs['academic_year'],
                }
            ).data

            if taught_class.is_class_master:
                response['class_master'].append(class_data)
            elif response.get(taught_class.class_grade):
                response[taught_class.class_grade].append(class_data)
            else:
                response[taught_class.class_grade] = [class_data]

        for key, value in response.items():
            value.sort(key=lambda x: (x['class_letter']))

        response_keys = list(response.keys())
        response_keys.remove('class_master')
        response_keys.sort(key=lambda x: (CLASS_GRADE_MAPPING[x]))
        response_data = {'class_master': response['class_master']}
        response_data.update({
            key: response[key]
            for key in response_keys
        })

        return Response(response_data)


class OwnStudyClassDetail(generics.RetrieveAPIView):
    permission_classes = (IsTeacher,)
    lookup_field = 'id'
    serializer_class = OwnStudyClassSerializer

    def get_queryset(self):
        return self.request.user.user_profile.study_classes.distinct()
