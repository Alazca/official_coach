from datetime import datetime

def validate_date(date_string):

    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except ValueError:
        return False
