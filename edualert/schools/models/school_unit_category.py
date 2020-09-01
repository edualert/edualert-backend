from django.db import models

from edualert.schools import constants


class SchoolUnitCategory(models.Model):
    name = models.CharField(max_length=128, unique=True)

    CategoryLevels = constants.CategoryLevels
    category_level = models.CharField(choices=CategoryLevels.choices, max_length=64)

    objects = models.Manager()

    def __str__(self):
        return f"SchoolUnitCategory {self.id} {self.name}"

    class Meta:
        verbose_name_plural = "School unit categories"
