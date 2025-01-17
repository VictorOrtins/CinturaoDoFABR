from datetime import datetime

def is_datetime(value):
    format_date = "%Y-%m-%d %H:%M:%S"

    try:
        datetime.strptime(value, format_date)
        return True
    except ValueError:
        return False