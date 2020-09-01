def study_class_post_save(sender, instance, created, **kwargs):
    if created:
        academic_program = instance.academic_program
        if academic_program is not None:
            academic_program.classes_count += 1
            academic_program.save()


def study_class_post_delete(sender, instance, **kwargs):
    academic_program = instance.academic_program
    if academic_program is not None and academic_program.classes_count > 0:
        academic_program.classes_count -= 1
        academic_program.save()
