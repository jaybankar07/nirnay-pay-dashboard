from pydantic import BaseModel, Field
from typing import Optional


class DiagnosisOutputSchema(BaseModel):
    root_cause: str = Field(..., description="Categorized root cause for payment/revenue failure")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    rationale: str = Field(..., description="Concise explanation of the diagnosis")


class DecisionRationaleSchema(BaseModel):
    rationale: str = Field(..., description="Concise decision rationale")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
