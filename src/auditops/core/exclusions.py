import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

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

class ExclusionManager:
    def __init__(self, exclusions: list[Exclusion] | None = None):
        self._test_exclusions = {}
        self._sample_exclusions = {}

        for exclusion in exclusions or []:
            if exclusion.is_expired:
                continue

            if exclusion.sample_id is None:
                self._test_exclusions[
                    (exclusion.provider, exclusion.test_id)
                ] = exclusion
            else:
                key = (
                    exclusion.provider,
                    exclusion.test_id,
                    frozenset(exclusion.sample_id.items())
                )
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
        key = (
            provider.lower(),
            test_id,
            frozenset(sample_id.items())
        )

        return self._sample_exclusions.get(key)

    def is_test_excluded(self, provider: str, test_id: str) -> bool:
        return self.get_test_exclusion(provider, test_id) is not None

    def is_sample_excluded(self, provider: str, test_id: str, sample_id: dict) -> bool:
        return (
            self.get_sample_exclusion(provider, test_id, sample_id) is not None
        )