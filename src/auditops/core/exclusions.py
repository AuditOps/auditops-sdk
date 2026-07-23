import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
import fnmatch

@dataclass(slots=True)
class Exclusion:
    test_id: str
    rationale: str
    sample_id: dict | None = None
    expires: date | None = None

    @property
    def is_expired(self) -> bool:
        return self.expires is not None and self.expires < date.today()

    @property
    def has_wildcards(self) -> bool:
        return self.sample_id is not None and any(
            "*" in str(v) for v in self.sample_id.values()
        )
    
    def matches_sample(self, sample_id: dict) -> bool:
        """Only valid for pattern exclusions."""
        for field, pattern in self.sample_id.items():
            value = sample_id.get(field)
            if value is None or not fnmatch.fnmatch(str(value), str(pattern)):
                return False
        return True


class ExclusionManager:
    def __init__(self, exclusions: list[Exclusion] | None = None):
        self._test_exclusions: dict[str, Exclusion] = {}
        self._sample_exclusions: dict[tuple[str, frozenset], Exclusion] = {}
        self._sample_patterns: dict[str, list[Exclusion]] = defaultdict(list)

        for exclusion in exclusions or []:
            if exclusion.is_expired:
                continue

            # Test-level exclusion
            if exclusion.sample_id is None:
                self._test_exclusions[exclusion.test_id] = exclusion
                continue

            # Sample-level exclusion
            if exclusion.has_wildcards:
                self._sample_patterns[exclusion.test_id].append(exclusion)
            else:
                key = (
                    exclusion.test_id,
                    frozenset(exclusion.sample_id.items()),
                )
                self._sample_exclusions[key] = exclusion

    @classmethod
    def load_exclusions(cls, filename: str | Path):
        filename = Path(filename)

        if not filename.exists():
            return cls()

        with filename.open() as f:
            data = json.load(f)

        exclusions = []

        def parse_exclusion(item, sample_id=None):
            expires = item.get("expires")
            if expires:
                expires = date.fromisoformat(expires)

            exclusions.append(
                Exclusion(
                    test_id=item["test_id"],
                    rationale=item["rationale"],
                    sample_id=sample_id,
                    expires=expires,
                )
            )

        for item in data.get("test_exclusions", []):
            parse_exclusion(item)

        for item in data.get("sample_exclusions", []):
            parse_exclusion(item, item["sample_id"])

        return cls(exclusions)

    def get_test_exclusion(self, test_id: str) -> Exclusion | None:
        return self._test_exclusions.get(test_id)

    def get_sample_exclusion(self, test_id: str, sample_id: dict) -> Exclusion | None:

        # Exact match first (fast)
        key = (test_id, frozenset(sample_id.items()))

        exclusion = self._sample_exclusions.get(key)
        if exclusion:
            return exclusion

        # Pattern match — only checks patterns registered under this test_id.
        for exclusion in self._sample_patterns.get((test_id), []):
            if exclusion.matches_sample(sample_id):
                return exclusion

        return None

    def is_test_excluded(self, test_id: str) -> bool:
        return self.get_test_exclusion(test_id) is not None

    def is_sample_excluded(self, test_id: str, sample_id: dict) -> bool:
        return self.get_sample_exclusion(test_id, sample_id) is not None