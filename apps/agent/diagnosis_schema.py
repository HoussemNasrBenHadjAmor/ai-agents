from typing import Literal

from pydantic import BaseModel, Field


DiagnosisStatus = Literal[
    "healthy",
    "degraded",
    "critical",
]


Severity = Literal[
    "critical",
    "warning",
    "info",
    "healthy",
]


ResourceType = Literal[
    "docker",
    "database",
    "network",
    "other",
]


class DiagnosisSummary(BaseModel):
    status: DiagnosisStatus

    total_issues: int = Field(
        ge=0
    )

    critical: int = Field(
        ge=0
    )

    warnings: int = Field(
        ge=0
    )

    healthy: int = Field(
        ge=0
    )

    headline: str = Field(
        min_length=1,
        max_length=300,
    )


class DiagnosisIssue(BaseModel):
    resource: str = Field(
        min_length=1,
        max_length=300,
    )

    resource_type: ResourceType

    status: str = Field(
        min_length=1,
        max_length=200,
    )

    severity: Severity

    problem: str = Field(
        min_length=1,
        max_length=500,
    )

    evidence: str = Field(
        min_length=1,
    )

    likely_cause: str = Field(
        min_length=1,
    )

    recommendation: str = Field(
        min_length=1,
    )


class Diagnosis(BaseModel):
    summary: DiagnosisSummary

    issues: list[
        DiagnosisIssue
    ]

    narrative: str = Field(
        min_length=1,
    )
