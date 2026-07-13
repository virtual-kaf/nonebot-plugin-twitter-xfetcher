from dataclasses import dataclass, field
from typing import List

@dataclass
class GroupConfig:
    group_id: str
    subs: List[str] = field(default_factory=list)
    unsubs: List[str] = field(default_factory=list)
    filter_water: bool = True
    master_on: bool = False
    radio_on: bool = False
