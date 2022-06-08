from datetime import datetime


def get_image_upload_path(instance, filename):

    return f"images/{instance.payment.person.name}/{datetime.now().year}/{datetime.now().month}/{filename}"
