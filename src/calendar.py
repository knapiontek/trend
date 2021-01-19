from datetime import datetime, timezone
from typing import Union

DT_FORMAT = '%Y-%m-%d %H:%M:%S %z'
D_FORMAT = '%Y-%m-%d'


class Calendar:
    @staticmethod
    def from_timestamp(ts: Union[int, float]) -> datetime:
        return datetime.fromtimestamp(ts, tz=timezone.utc)

    @staticmethod
    def to_timestamp(dt: datetime) -> int:
        assert dt.tzinfo
        return int(dt.timestamp())

    @staticmethod
    def utc_now() -> datetime:
        return datetime.now(tz=timezone.utc)

    @staticmethod
    def parse_datetime(dt: str) -> datetime:
        return datetime.strptime(dt, DT_FORMAT).replace(tzinfo=timezone.utc)

    @staticmethod
    def parse_date(d: str) -> datetime:
        return datetime.strptime(d, D_FORMAT).replace(tzinfo=timezone.utc)

    @staticmethod
    def format(value: Union[int, float, datetime]) -> str:
        if isinstance(value, datetime):
            return value.strftime(DT_FORMAT)
        elif isinstance(value, (int, float)):
            dt = Calendar.from_timestamp(value)
            return dt.strftime(DT_FORMAT)
        else:
            raise Exception(f'Cannot format {value}')
