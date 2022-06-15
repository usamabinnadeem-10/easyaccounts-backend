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


def is_string_a_number(s):
    """Returns True is string is a number."""
    return s.replace(".", "", 1).isdigit()


def convert_qp_dict_to_qp(qpDict):
    dict = {}
    for key, value in qpDict.items():
        val = value[0]
        if is_string_a_number(val):
            dict[key] = float(val)
        else:
            dict[key] = val
    return dict
