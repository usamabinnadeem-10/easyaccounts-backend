from datetime import datetime


def convert_date_to_datetime(date, return_none=False, time=None):
    """get datetime format"""
    return (
        datetime.strptime(f"{date}", "%Y-%m-%d %H:%M:%S")
        if date
        else None
        if return_none
        else datetime.now()
    )
