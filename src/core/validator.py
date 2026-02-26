#!/usr/bin/env python3
"""
Finding validator: uses an LLM (Bedrock, Vertex, or Ollama) to classify scan findings
as true or false positive. Used optionally before posting PR comments.
"""

import hashlib
import os
from typing import Dict, List, Optional, Set, Tuple

from .config import (
    AI_SAST_VALIDATOR_LLM,
    AI_SAST_VALIDATOR_BEDROCK_MODEL_ID,
    AI_SAST_VALIDATOR_GEMINI_MODEL,
    PROJECT_ID,
    LOCATION,
    AWS_REGION,
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
)


def _vuln_id(file_path: str, issue: str, location: str) -> str:
    unique = f"{file_path}-{issue}-{location}"
    return hashlib.sha1(unique.encode()).hexdigest()[:8]


def _validator_prompt(vuln: Dict) -> str:
    return (
        "You are a security expert. A static analysis tool reported the following finding. "
        "Is this a TRUE POSITIVE security vulnerability that could be exploited in context? "
        "Consider: is the finding accurate, exploitable, and not a false positive (e.g. test code, already mitigated)?\n\n"
        "Finding:\n"
        f"- File: {vuln.get('file_path', 'N/A')}\n"
        f"- Issue: {vuln.get('issue', 'N/A')}\n"
        f"- Location: {vuln.get('location', 'N/A')}\n"
        f"- Severity: {vuln.get('severity', 'N/A')}\n"
        f"- Risk: {vuln.get('risk', 'N/A')}\n\n"
        "Reply with exactly one word: TRUE or FALSE. "
        "If TRUE, on the next line add a single short sentence (validator proof) explaining why this is a true positive. "
        "If FALSE, on the next line add a single short sentence explaining why this is a false positive (e.g. test code, mitigated, not exploitable)."
    )


def _parse_response(response: str) -> Tuple[bool, str]:
    """Returns (is_true_positive, reasoning). Reasoning is 1-2 lines after TRUE or FALSE."""
    if not response:
        return False, ""
    text = response.strip()
    r = text.upper()
    is_tp = r.startswith("TRUE") and not r.startswith("FALSE")
    # Take the rest of the response after TRUE/FALSE (and optional newline) as reasoning, max 1-2 lines
    rest = response.strip()
    if rest.upper().startswith("TRUE"):
        rest = rest[4:].lstrip("\n\r\t ").strip()
    elif rest.upper().startswith("FALSE"):
        rest = rest[5:].lstrip("\n\r\t ").strip()
    else:
        rest = ""
    reasoning = ""
    if rest:
        lines = [ln.strip() for ln in rest.split("\n") if ln.strip()][:2]
        reasoning = " ".join(lines) if lines else ""
    return is_tp, reasoning


def validate_findings(
    vulnerabilities_by_severity: Dict[str, List[Dict]],
    repo_url: Optional[str] = None,
) -> Optional[Tuple[Set[str], Dict[str, str], Dict[str, str], str]]:
    """
    Run validator LLM on each finding.

    Returns:
        None if validation is disabled / not configured / errors (caller should then use all findings).
        Otherwise a tuple:
          - validated_ids: set of vuln_ids classified as true positive
          - reasoning_by_id: vuln_id -> 1-2 line "validator proof" (only for true positives)
          - all_results_by_id: vuln_id -> validator result for DB ("reasoning" or "false_positive" or "error")
          - validator_llm: string identifying the validator LLM (e.g. "bedrock:anthropic.claude-3-5-sonnet-...")
    """
    all_vulns: List[Dict] = []
    for sev, vulns in vulnerabilities_by_severity.items():
        for v in vulns:
            v = dict(v)
            v["severity"] = sev
            all_vulns.append(v)

    if not all_vulns:
        return (set(), {}, {}, "")

    provider = (os.getenv("AI_SAST_VALIDATOR_LLM") or "bedrock").lower()
    validator_llm_label = ""

    try:
        if provider == "bedrock":
            from ..integrations.bedrock import BedrockClaudeClient
            client = BedrockClaudeClient(
                region_name=AWS_REGION,
                model_id=AI_SAST_VALIDATOR_BEDROCK_MODEL_ID,
            )
            validator_llm_label = f"bedrock:{AI_SAST_VALIDATOR_BEDROCK_MODEL_ID}"
            print(f"🔧 Validator LLM: AWS Bedrock (Claude), model: {AI_SAST_VALIDATOR_BEDROCK_MODEL_ID}")

            def generate(prompt: str) -> str:
                return client.generate_with_bedrock(prompt, model_name=AI_SAST_VALIDATOR_BEDROCK_MODEL_ID)

        elif provider == "vertex":
            from .vertex import VertexAIClient
            client = VertexAIClient(project_id=PROJECT_ID, location=LOCATION)
            validator_llm_label = f"vertex:{AI_SAST_VALIDATOR_GEMINI_MODEL}"
            print(f"🔧 Validator LLM: Vertex AI (Gemini), model: {AI_SAST_VALIDATOR_GEMINI_MODEL}")

            def generate(prompt: str) -> str:
                return client.generate_with_gemini(prompt, model_name=AI_SAST_VALIDATOR_GEMINI_MODEL)

        elif provider == "ollama":
            from ..integrations.ollama import OllamaClient
            client = OllamaClient(base_url=OLLAMA_BASE_URL, model=OLLAMA_MODEL)
            validator_llm_label = f"ollama:{OLLAMA_MODEL}"
            print(f"🔧 Validator LLM: Ollama (local), model: {OLLAMA_MODEL}")

            def generate(prompt: str) -> str:
                return client.generate_with_ollama(prompt, temperature=0.1)

        else:
            print(f"⚠️ Validator LLM unknown: {provider}. Skipping validation.")
            return None

    except Exception as e:
        print(f"⚠️ Validator not configured or error initializing: {e}. Skipping validation.")
        return None

    true_positive_ids: Set[str] = set()
    reasoning_by_id: Dict[str, str] = {}
    all_results_by_id: Dict[str, str] = {}

    for vuln in all_vulns:
        vid = _vuln_id(
            vuln.get("file_path", ""),
            vuln.get("issue", ""),
            vuln.get("location", ""),
        )
        try:
            prompt = _validator_prompt(vuln)
            response = generate(prompt)
            is_tp, reasoning = _parse_response(response)
            if is_tp:
                true_positive_ids.add(vid)
                reasoning_by_id[vid] = reasoning or "Validated as true positive."
                all_results_by_id[vid] = reasoning_by_id[vid]
                print(f"  [Validator] {vid}: TRUE POSITIVE — {reasoning_by_id[vid]}")
            else:
                fp_reasoning = reasoning or "Rejected as false positive."
                all_results_by_id[vid] = f"false_positive: {fp_reasoning}"
                print(f"  [Validator] {vid}: FALSE POSITIVE (rejected) — {fp_reasoning}")
        except Exception as e:
            all_results_by_id[vid] = f"error:{str(e)[:200]}"
            print(f"  [Validator] {vid}: ERROR — {e}")
    return (true_positive_ids, reasoning_by_id, all_results_by_id, validator_llm_label)
