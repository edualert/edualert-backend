def get_school_cycle_for_class_grade(class_grade):
    for cycle in (range(0, 5), range(5, 9), range(9, 14)):
        if class_grade in cycle:
            return cycle
    return None
