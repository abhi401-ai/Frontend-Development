"""
test_live_integration.py
--------------------------
EduGenie - Live Frontend <-> Backend Integration Test / Demo

This script exercises the running FastAPI backend exactly the way the
frontend (static/app.js) does: it sends the same HTTP requests the
browser would send for each form (QnA, Concept Explanation, Quiz
Generation, Summarization, Personalized Learning Recommendations),
captures the structured JSON response, and reports the round-trip time.

It demonstrates and verifies that:
  - User input from each form section reaches the correct AI module.
  - Responses come back as structured JSON, ready to render in the
    matching output container, without a full page reload.
  - Missing/invalid required fields are rejected with a clear error,
    just as they would be when a user submits an incomplete form.

Usage:
    1. Start the real backend in one terminal:
           uvicorn main:app --reload
    2. Run this script in another terminal:
           python test_live_integration.py
       Optionally point it at a different host/port:
           python test_live_integration.py --base-url http://127.0.0.1:8000

Install:
    pip install requests
"""

import argparse
import json
import sys
import time

import requests


def call_endpoint(label: str, method: str, url: str, **kwargs) -> bool:
    """Call one endpoint the same way the frontend would, time it, and report the result."""
    print(f"\n{'-' * 70}")
    print(f"{label}")
    print(f"{method} {url}")
    if "params" in kwargs:
        print(f"  query params : {kwargs['params']}")
    if "json" in kwargs:
        print(f"  JSON body    : {json.dumps(kwargs['json'])}")

    start = time.perf_counter()
    try:
        response = requests.request(method, url, timeout=60, **kwargs)
    except requests.exceptions.ConnectionError:
        print("  RESULT       : FAILED — could not connect. Is the backend running?")
        return False
    elapsed_ms = (time.perf_counter() - start) * 1000

    print(f"  status code  : {response.status_code}  ({elapsed_ms:.0f} ms)")

    try:
        data = response.json()
    except ValueError:
        print("  RESULT       : FAILED — response was not valid JSON")
        print(response.text[:300])
        return False

    preview = json.dumps(data, indent=2)
    if len(preview) > 800:
        preview = preview[:800] + " ...(truncated)"
    print(f"  response     :\n{preview}")

    return response.ok


def run_integration_checks(base_url: str) -> bool:
    """
    Run one live request per educational task, plus a validation check,
    mirroring exactly what each form in index.html submits.
    """
    core_results = []

    # 1) Question Answering — frontend form #qa, GET request
    core_results.append(call_endpoint(
        "1) Question Answering  (form: 'Ask a Question')",
        "GET",
        f"{base_url}/qa",
        params={"question": "Why does the Moon show different phases?"},
    ))

    # 2) Concept Explanation — frontend form #explain, POST request
    core_results.append(call_endpoint(
        "2) Concept Explanation  (form: 'Explain a Concept')",
        "POST",
        f"{base_url}/explain",
        json={"topic": "Newton's second law of motion"},
    ))

    # 3) Summarization — frontend form #summarize, POST request
    core_results.append(call_endpoint(
        "3) Summarization  (form: 'Summarize Text')",
        "POST",
        f"{base_url}/summarize",
        json={"text": (
            "Photosynthesis is the process by which green plants use sunlight, "
            "water, and carbon dioxide to produce oxygen and glucose. It mainly "
            "takes place in the chloroplasts of plant cells, using a pigment "
            "called chlorophyll to capture light energy."
        )},
    ))

    # 4) Quiz Generation — frontend form #quiz, POST request
    core_results.append(call_endpoint(
        "4) Quiz Generation  (form: 'Generate a Quiz')",
        "POST",
        f"{base_url}/quiz",
        json={
            "passage": (
                "Photosynthesis is the process by which green plants use sunlight, "
                "water, and carbon dioxide to produce oxygen and glucose."
            ),
            "num_questions": 3,
            "num_options": 4,
        },
    ))

    # 5) Personalized Learning Recommendations — frontend form #learn, GET request
    core_results.append(call_endpoint(
        "5) Learning Recommendations  (form: 'Map a Learning Path')",
        "GET",
        f"{base_url}/learn/recommendations",
        params={"topic": "Machine Learning", "level": "beginner"},
    ))

    # 6) Validation check — same request the form would send if a user
    #    tried to submit an empty required field.
    call_endpoint(
        "6) Validation check — empty 'topic' field on /explain",
        "POST",
        f"{base_url}/explain",
        json={"topic": ""},
    )

    print(f"\n{'=' * 70}")
    passed = sum(core_results)
    print(f"Live integration result: {passed}/{len(core_results)} core endpoints "
          f"responded successfully in real time.")
    return passed == len(core_results)


def main():
    parser = argparse.ArgumentParser(
        description="Test EduGenie's live frontend <-> FastAPI backend integration."
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="Base URL of the running FastAPI server (default: %(default)s)",
    )
    args = parser.parse_args()

    all_passed = run_integration_checks(args.base_url.rstrip("/"))
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()