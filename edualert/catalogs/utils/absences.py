from edualert.catalogs.models import StudentCatalogPerSubject
from edualert.catalogs.tasks import update_absences_counts_for_students_task


def change_absences_counts_on_add(catalog, absence):
    catalog.abs_count_annual += 1
    if absence.semester == 1:
        catalog.abs_count_sem1 += 1
        if absence.is_founded:
            catalog.founded_abs_count_sem1 += 1
            catalog.founded_abs_count_annual += 1
        else:
            catalog.unfounded_abs_count_sem1 += 1
            catalog.unfounded_abs_count_annual += 1
    else:
        catalog.abs_count_sem2 += 1
        if absence.is_founded:
            catalog.founded_abs_count_sem2 += 1
            catalog.founded_abs_count_annual += 1
        else:
            catalog.unfounded_abs_count_sem2 += 1
            catalog.unfounded_abs_count_annual += 1
    catalog.save()
    update_absences_counts_for_students_task.delay([catalog.id])


def change_absences_counts_on_authorize(catalog, absence):
    if absence.semester == 1:
        if catalog.unfounded_abs_count_sem1 > 0:
            catalog.unfounded_abs_count_sem1 -= 1
        catalog.founded_abs_count_sem1 += 1
    else:
        if catalog.unfounded_abs_count_sem2 > 0:
            catalog.unfounded_abs_count_sem2 -= 1
        catalog.founded_abs_count_sem2 += 1

    if catalog.unfounded_abs_count_annual > 0:
        catalog.unfounded_abs_count_annual -= 1
    catalog.founded_abs_count_annual += 1

    catalog.save()
    update_absences_counts_for_students_task.delay([catalog.id])


def change_absences_counts_on_delete(catalog, semester, is_founded):
    if catalog.abs_count_annual > 0:
        catalog.abs_count_annual -= 1

    if semester == 1:
        if catalog.abs_count_sem1 > 0:
            catalog.abs_count_sem1 -= 1
        if is_founded:
            if catalog.founded_abs_count_sem1 > 0:
                catalog.founded_abs_count_sem1 -= 1
            if catalog.founded_abs_count_annual > 0:
                catalog.founded_abs_count_annual -= 1
        else:
            if catalog.unfounded_abs_count_sem1 > 0:
                catalog.unfounded_abs_count_sem1 -= 1
            if catalog.unfounded_abs_count_annual > 0:
                catalog.unfounded_abs_count_annual -= 1
    else:
        if catalog.abs_count_sem2 > 0:
            catalog.abs_count_sem2 -= 1
        if is_founded:
            if catalog.founded_abs_count_sem2 > 0:
                catalog.founded_abs_count_sem2 -= 1
            if catalog.founded_abs_count_annual > 0:
                catalog.founded_abs_count_annual -= 1
        else:
            if catalog.unfounded_abs_count_sem2 > 0:
                catalog.unfounded_abs_count_sem2 -= 1
            if catalog.unfounded_abs_count_annual > 0:
                catalog.unfounded_abs_count_annual -= 1

    catalog.save()
    update_absences_counts_for_students_task.delay([catalog.id])


def change_absence_counts_on_bulk_add(absences, semester):
    catalogs_to_update = []

    if semester == 1:
        for absence in absences:
            catalog = absence.catalog_per_subject
            catalog.abs_count_sem1 += 1
            catalog.abs_count_annual += 1
            if absence.is_founded:
                catalog.founded_abs_count_sem1 += 1
                catalog.founded_abs_count_annual += 1
            else:
                catalog.unfounded_abs_count_sem1 += 1
                catalog.unfounded_abs_count_annual += 1
            catalogs_to_update.append(catalog)

        fields_to_update = ['abs_count_sem1', 'abs_count_annual',
                            'unfounded_abs_count_sem1', 'unfounded_abs_count_annual',
                            'founded_abs_count_sem1', 'founded_abs_count_annual']
    else:
        for absence in absences:
            catalog = absence.catalog_per_subject
            catalog.abs_count_sem2 += 1
            catalog.abs_count_annual += 1
            if absence.is_founded:
                catalog.founded_abs_count_sem2 += 1
                catalog.founded_abs_count_annual += 1
            else:
                catalog.unfounded_abs_count_sem2 += 1
                catalog.unfounded_abs_count_annual += 1
            catalogs_to_update.append(catalog)

        fields_to_update = ['abs_count_sem2', 'abs_count_annual',
                            'unfounded_abs_count_sem2', 'unfounded_abs_count_annual',
                            'founded_abs_count_sem2', 'founded_abs_count_annual']

    StudentCatalogPerSubject.objects.bulk_update(catalogs_to_update, fields_to_update)
    catalog_ids = [catalog.id for catalog in catalogs_to_update]
    update_absences_counts_for_students_task.delay(catalog_ids)
