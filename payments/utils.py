from datetime import datetime


def get_image_upload_path(instance, filename):
    return f"payments/{datetime.now().year}/{datetime.now().month}/{filename}"
