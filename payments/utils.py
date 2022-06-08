from datetime import datetime


def get_image_upload_path(instance, filename):

    return f"images/{datetime.now().year}/{datetime.now().month}/{instance.payment.person.name}/{filename}"
