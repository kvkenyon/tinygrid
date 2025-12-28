import pandas as pd

from tinygrid.utils.dates import parse_date


def test_parse_date_defaults_when_none():
    ts = parse_date(None)
    assert isinstance(ts, pd.Timestamp)
    assert ts.tz is not None
