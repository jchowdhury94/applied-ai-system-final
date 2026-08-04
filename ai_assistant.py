"""Claude API integration and assistant orchestration for PawPal+.

Wires the pipeline together:

    question -> retrieval.retrieve_context() -> grounded prompt
             -> Claude API -> validators.validate_answer()
             -> Claude answer, or a safe deterministic fallback

This module is read-only: it never modifies Owner, Pet, Task, or Scheduler
state, and the assistant it powers has no ability to add, delete, complete,
or reschedule anything - it only answers questions about existing data.
"""

import os

from dotenv import load_dotenv

load_dotenv()

from logger_config import get_logger
import retrieval
import validators

logger = get_logger(__name__)

# Keep the model name in exactly one place. ANTHROPIC_MODEL overrides this;
# the `model` parameter to answer_question() overrides both. Haiku 4.5 is a
# currently supported, low-cost model well suited to this classroom demo;
# set ANTHROPIC_MODEL in .env to use a different one (e.g. claude-opus-5).
DEFAULT_MODEL = "claude-haiku-4-5"

MAX_ANSWER_TOKENS = 500

FALLBACK_BLANK_QUESTION = "blank_question"
FALLBACK_UNSUPPORTED_QUESTION = "unsupported_question"
FALLBACK_NO_CONTEXT = "no_context"
FALLBACK_MISSING_API_KEY = "missing_api_key"
FALLBACK_API_ERROR = "api_error"
FALLBACK_EMPTY_RESPONSE = "empty_response"
FALLBACK_RESPONSE_PARSE_ERROR = "response_parse_error"
FALLBACK_VALIDATION_FAILED = "validation_failed"

_SYSTEM_PROMPT = (
    "You are the PawPal+ AI assistant. Answer only using the PawPal+ context "
    "supplied below the question in this prompt. Never invent pets, tasks, "
    "times, dates, completion states, or scheduling conflicts that are not "
    "present in that context. You must not claim to add, delete, complete, "
    "reschedule, or otherwise change any PawPal+ data - you are strictly "
    "read-only and have no ability to modify data. Never provide veterinary "
    "diagnosis or medication advice. If the supplied context does not "
    "contain enough information to answer, say so plainly instead of "
    "guessing. Keep answers concise. You may paraphrase the retrieved facts "
    "in your own words, but always clearly distinguish stored PawPal+ facts "
    "(from the context) from any general suggestions you add on top."
)


def _unsupported_fallback_answer():
    return validators.format_fallback_answer(
        {"intent": retrieval.INTENT_UNSUPPORTED, "records": []}
    )


def _new_result(retrieval_result, model_name):
    return {
        "success": False,
        "answer": None,
        "intent": retrieval_result.get("intent") if retrieval_result else None,
        "detected_pet": retrieval_result.get("detected_pet") if retrieval_result else None,
        "retrieval_result": retrieval_result,
        "validation_result": None,
        "fallback_used": False,
        "fallback_reason": None,
        "model": model_name,
        "error": None,
    }


def _fall_back(result, retrieval_result, reason, error_message):
    result["fallback_used"] = True
    result["fallback_reason"] = reason
    result["answer"] = validators.format_fallback_answer(retrieval_result)
    result["error"] = error_message
    logger.info("Deterministic fallback used. fallback_reason=%s", reason)
    logger.info("Processing completed. success=False fallback_used=True")
    return result


def _build_user_prompt(question, retrieval_result):
    """Build a compact, grounded user-turn prompt from a retrieval result."""
    intent = retrieval_result.get("intent")
    detected_pet = retrieval_result.get("detected_pet")

    lines = [f"Question: {question}", f"Detected intent: {intent}"]
    if detected_pet:
        lines.append(f"Detected pet: {detected_pet}")
    lines.append("")
    lines.append("PawPal+ context:")
    lines.append(retrieval_result.get("context_text") or "")
    return "\n".join(lines)


def _extract_text(response):
    """Safely pull and join every text block from a Claude Messages API response.

    Returns None if the response has no content, no text blocks, or the
    content is shaped in a way this function does not recognize. Tolerates
    both SDK content-block objects and plain dicts so a variety of mocked
    response shapes work without depending on one exact object type.
    """
    content = getattr(response, "content", None)
    if content is None and isinstance(response, dict):
        content = response.get("content")
    if not content:
        return None

    texts = []
    for block in content:
        if isinstance(block, dict):
            block_type = block.get("type")
            text = block.get("text")
        else:
            block_type = getattr(block, "type", None)
            text = getattr(block, "text", None)

        if block_type == "text" and text:
            texts.append(text)

    if not texts:
        return None

    joined = "\n".join(texts).strip()
    return joined or None


def answer_question(question, owner, reference_date=None, client=None, model=None):
    """Answer a PawPal+ question, grounded in retrieved data, with a safe fallback.

    Never mutates `owner` or any Pet/Task/Scheduler state. Returns a
    dictionary describing what happened - see the module docstring for the
    pipeline this function drives, and the FALLBACK_* constants above for
    the stable `fallback_reason` values it can report.
    """
    model_name = model or os.environ.get("ANTHROPIC_MODEL") or DEFAULT_MODEL
    question_length = len(question) if question else 0
    logger.info("Question processing started. question_length=%d", question_length)
    logger.info("Model selected: %s", model_name)

    if question is None or not question.strip():
        result = _new_result(None, model_name)
        return _fall_back(
            result,
            {"intent": retrieval.INTENT_UNSUPPORTED, "records": []},
            FALLBACK_BLANK_QUESTION,
            "The question was blank.",
        )

    retrieval_result = retrieval.retrieve_context(question, owner, reference_date=reference_date)
    result = _new_result(retrieval_result, model_name)
    logger.info("Detected intent: %s", retrieval_result.get("intent"))

    if not retrieval_result.get("supported"):
        return _fall_back(
            result,
            retrieval_result,
            FALLBACK_UNSUPPORTED_QUESTION,
            retrieval_result.get("message") or "This question is not supported.",
        )

    if not retrieval_result.get("records"):
        return _fall_back(
            result,
            retrieval_result,
            FALLBACK_NO_CONTEXT,
            retrieval_result.get("message") or "No relevant PawPal+ data was found.",
        )

    if client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return _fall_back(
                result,
                retrieval_result,
                FALLBACK_MISSING_API_KEY,
                "The Claude API key is not configured.",
            )
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=api_key)
        except Exception as exc:
            logger.error(
                "Claude API client could not be initialized (%s).", type(exc).__name__
            )
            return _fall_back(
                result,
                retrieval_result,
                FALLBACK_API_ERROR,
                "The Claude API client could not be initialized.",
            )

    user_prompt = _build_user_prompt(question, retrieval_result)

    logger.info("Claude request attempted.")
    try:
        response = client.messages.create(
            model=model_name,
            max_tokens=MAX_ANSWER_TOKENS,
            system=_SYSTEM_PROMPT,
            thinking={"type": "disabled"},
            messages=[{"role": "user", "content": user_prompt}],
        )
    except Exception as exc:
        logger.error("Claude API request failed (%s).", type(exc).__name__)
        return _fall_back(
            result,
            retrieval_result,
            FALLBACK_API_ERROR,
            "The Claude API request failed. Showing a fallback answer instead.",
        )
    logger.info("Claude request succeeded.")

    content = getattr(response, "content", None)
    if content is None and isinstance(response, dict):
        content = response.get("content")

    if content is None:
        logger.info("Empty or malformed Claude response: no content field.")
        return _fall_back(
            result,
            retrieval_result,
            FALLBACK_RESPONSE_PARSE_ERROR,
            "The Claude API response could not be read.",
        )

    if len(content) == 0:
        logger.info("Empty or malformed Claude response: no content blocks.")
        return _fall_back(
            result,
            retrieval_result,
            FALLBACK_EMPTY_RESPONSE,
            "The Claude API returned an empty response.",
        )

    claude_answer = _extract_text(response)
    if not claude_answer:
        logger.info("Empty or malformed Claude response: no readable text.")
        return _fall_back(
            result,
            retrieval_result,
            FALLBACK_RESPONSE_PARSE_ERROR,
            "The Claude API response did not contain a readable answer.",
        )

    validation_result = validators.validate_answer(claude_answer, retrieval_result)
    result["validation_result"] = validation_result

    if not validation_result["valid"]:
        logger.info("Validation failed for the generated answer.")
        return _fall_back(
            result,
            retrieval_result,
            FALLBACK_VALIDATION_FAILED,
            "The generated answer did not pass validation; showing a fallback answer.",
        )
    logger.info("Validation passed for the generated answer.")

    result["success"] = True
    result["answer"] = claude_answer
    logger.info("Processing completed. success=True fallback_used=False")
    return result
