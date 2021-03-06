from .pupils_statistics import PupilStatisticsForORSSerializer, PupilStatisticsForSchoolEmployeeSerializer, \
    StudentsAveragesSerializer, StudentsAbsencesSerializer, StudentsBehaviorGradeSerializer,\
    SchoolStudentAtRiskSerializer, StudentAtRiskSerializer
from .school_situation import SchoolSituationSerializer, StudentStatisticsSerializer, StudentSubjectsAtRiskSerializer
from .school_unit_statistics import SchoolUnitStatsAverageSerializer, SchoolUnitStatsAbsencesSerializer, \
    RegisteredSchoolUnitLastChangeInCatalogSerializer, RegisteredSchoolUnitRiskSerializer
from .academic_program_statistics import AcademicProgramsAverageSerializer, AcademicProgramsAbsencesSerializer, \
    AcademicProgramsRiskSerializer
from .study_class_statistics import StudyClassesAveragesSerializer, StudyClassesAbsencesSerializer, StudyClassesRiskSerializer
from .profile_statistics import UserProfileLastChangeInCatalogSerializer, ParentLastOnlineSerializer
