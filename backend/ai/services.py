import json
import os
from typing import Any

from pydantic import BaseModel, Field


def _safe_json_loads(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"executive_summary": value}
    return {"executive_summary": str(value)}


class IncidentAnalysis(BaseModel):
    executive_summary: str
    observed_symptoms: list[str] = Field(default_factory=list)
    likely_root_cause_hypotheses: list[str] = Field(default_factory=list)
    evidence_supporting_each_hypothesis: dict[str, list[str]] = Field(default_factory=dict)
    alternative_explanations: list[str] = Field(default_factory=list)
    recommended_diagnostic_steps: list[str] = Field(default_factory=list)
    potential_remediation: list[str] = Field(default_factory=list)
    severity_assessment: str = "medium"
    confidence: str = "medium"
    missing_information: list[str] = Field(default_factory=list)


def generate_incident_analysis(incident, logs, stats):
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("Google API key is not configured. Set GOOGLE_API_KEY to enable AI incident analysis.")

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.prompts import ChatPromptTemplate
    except ImportError as exc:
        raise RuntimeError("LangChain Gemini integration is unavailable in this environment.") from exc

    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.1, api_key=api_key)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an incident investigation assistant. Distinguish facts from hypotheses. Do not invent metrics, logs, or confirmed root causes. Use only the evidence provided."),
        ("user", "Analyze this software incident. Output valid JSON matching the structure in the task.\n\nIncident: {incident}\nLogs: {logs}\nStats: {stats}\n")
    ])
    response = llm.invoke(prompt.format(incident=str(incident), logs=str(logs[:20]), stats=str(stats)))
    payload = _safe_json_loads(response.content)
    return IncidentAnalysis.model_validate(payload)
