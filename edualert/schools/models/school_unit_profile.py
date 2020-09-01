from django.db import models


class SchoolUnitProfile(models.Model):
    name = models.CharField(max_length=64)
    category = models.ForeignKey("schools.SchoolUnitCategory", on_delete=models.CASCADE,
                                 related_name="academic_profiles", related_query_name="academic_profile")

    objects = models.Manager()

    def __str__(self):
        return f"SchoolUnitProfile {self.id} {self.name}"
