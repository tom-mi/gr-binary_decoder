from dataclasses import dataclass


@dataclass
class ExpectedTag(object):
    offset: int
    key: str
    value: object
