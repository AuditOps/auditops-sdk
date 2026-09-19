from dataclasses import dataclass, field

@dataclass
class GoogleWorkspaceConfig:
    """
    Configuration options used by GoogleWorkspaceCollector and GoogleWorkspaceTester.
    
    """

    required_group_emails: list[str] | None = None
    min_group_members: int = 2
    mfa_grace_period: int = 7