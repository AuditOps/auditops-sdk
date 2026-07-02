import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
import fnmatch

@dataclass
class Exclusion:
    provider: str
    test_id: str
    rationale: str
    sample_id: dict | None = None
    expires: date | None = None

    @property
    def is_expired(self) -> bool:
        return self.expires is not None and self.expires < date.today()

    @property
    def is_pattern(self) -> bool:
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
        self._test_exclusions: dict[tuple, Exclusion] = {}
        self._sample_exclusions: dict[tuple, Exclusion] = {}
        self._sample_patterns: dict[tuple, list[Exclusion]] = defaultdict(list)

        for exclusion in exclusions or []:
            if exclusion.is_expired:
                continue

            key_prefix = (exclusion.provider, exclusion.test_id)

            if exclusion.sample_id is None:
                self._test_exclusions[key_prefix] = exclusion
            elif exclusion.is_pattern:
                self._sample_patterns[key_prefix].append(exclusion)
            else:
                key = key_prefix + (frozenset(exclusion.sample_id.items()),)
                self._sample_exclusions[key] = exclusion

    @classmethod
    def load_exclusions(cls, filename: str | Path):
        filename = Path(filename)

        if not filename.exists():
            return cls()

        with open(filename, "r") as f:
            data = json.load(f)

        exclusions = []
        for item in data.get("exclusions", []):
            expires = item.get("expires")
            if expires:
                expires = date.fromisoformat(expires)

            exclusions.append(
                Exclusion(
                    provider=item["provider"].lower(),
                    test_id=item["test_id"],
                    sample_id=item.get("sample_id"),
                    rationale=item["rationale"],
                    expires=expires,
                )
            )

        return cls(exclusions)

    def get_test_exclusion(self, provider: str, test_id: str) -> Exclusion | None:
        return self._test_exclusions.get(
            (provider.lower(), test_id)
        )

    def get_sample_exclusion(self, provider: str, test_id: str, sample_id: dict) -> Exclusion | None:
        provider = provider.lower()

        # Exact match first (fast)
        key = (provider.lower(), test_id, frozenset(sample_id.items()))

        exclusion = self._sample_exclusions.get(key)
        if exclusion:
            return exclusion

        # Pattern match — only checks patterns registered under this (provider, test_id)
        for exclusion in self._sample_patterns.get((provider, test_id), []):
            if exclusion.matches_sample(sample_id):
                return exclusion

        return None

    def is_test_excluded(self, provider: str, test_id: str) -> bool:
        return self.get_test_exclusion(provider, test_id) is not None

    def is_sample_excluded(self, provider: str, test_id: str, sample_id: dict) -> bool:
        return self.get_sample_exclusion(provider, test_id, sample_id) is not None