from management.models import Task

DEFAULT_TASKS = [
    ("Partnership", 3),
    ("Training simulation", 75),
    ("BI Session", 10),
    ("Self Training", 75),
    ("Internal Training", 6),
    ("Orientation", 5),
    ("Backend Testing", 75),
    ("KT Session", 10),
    ("IT Project", 9),
    ("Tech Support", 20),
    ("PBR", 10),
]

def create_default_tasks_for_user(user):

    for title, max_point in DEFAULT_TASKS:

        Task.objects.get_or_create(
            employee=user,
            activity_name=title,
            defaults={
                "point": 0,
                "mxpoint": max_point,
                "mxearning": max_point,
                "description": f"{title} task",
            }
        )
