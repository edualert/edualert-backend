from edualert.profiles.tasks import send_alert_for_labels


def post_add_labels(sender, instance, action, pk_set, **kwargs):
    if action == 'post_add':
        send_alert_for_labels(instance.id, pk_set)
