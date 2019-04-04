from datetime import datetime, date, timedelta


def coerce_timestamp(value):
    return datetime.fromtimestamp(value)


def coerce_interval(value):
    if isinstance(value, (int, float)):
        return timedelta(seconds=value)
    else:
        assert 0


def coerce_date(value):
    return date.fromtimestamp(value)


TYPE_MAPPING = {
    'timestamp': coerce_timestamp,
    'date': coerce_date,
    'interval': coerce_interval
}


def coerce(type, value):
    if value is None:
        return None
    if type not in TYPE_MAPPING:
        return value
    return TYPE_MAPPING[type](value)
