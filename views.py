import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

from .scoring import analyze_tasks as analyze_tasks_algo


def parse_request_body(request):
    """Helper: parse JSON body and return (data, error_msg)."""
    try:
        body = request.body.decode("utf-8")
        if not body:
            return {}, None  # allow empty body as {}
        data = json.loads(body)
        if not isinstance(data, dict):
            return None, "Request body must be a JSON object"
        return data, None
    except json.JSONDecodeError:
        return None, "Invalid JSON"


@csrf_exempt
def analyze_tasks_view(request):
    """
    POST /api/tasks/analyze/
    Body: {"strategy": "...", "tasks": [ ... ]}
    """
    # ✅ CORS preflight: browser sends OPTIONS first
    if request.method == "OPTIONS":
        # Tell browser it's okay
        response = JsonResponse({}, status=200)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    if request.method != "POST":
        return HttpResponseBadRequest("Only POST is allowed")

    data, error = parse_request_body(request)
    if error:
        return HttpResponseBadRequest(error)

    tasks = data.get("tasks")
    strategy = data.get("strategy", "smart_balance")

    if not isinstance(tasks, list):
        return HttpResponseBadRequest("Field 'tasks' must be a list")

    scored_tasks = analyze_tasks_algo(tasks, strategy=strategy)

    response = JsonResponse(
        {
            "strategy": strategy,
            "count": len(scored_tasks),
            "tasks": scored_tasks,
        }
    )
    # (Extra safety, though corsheaders should handle it)
    response["Access-Control-Allow-Origin"] = "*"
    return response


@csrf_exempt
def suggest_tasks_view(request):
    """
    POST /api/tasks/suggest/
    Body: {"strategy": "...", "tasks": [ ... ]}
    Returns: top 3 tasks.
    """
    # ✅ CORS preflight here too
    if request.method == "OPTIONS":
        response = JsonResponse({}, status=200)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    if request.method != "POST":
        return HttpResponseBadRequest("Only POST is allowed")

    data, error = parse_request_body(request)
    if error:
        return HttpResponseBadRequest(error)

    tasks = data.get("tasks")
    strategy = data.get("strategy", "smart_balance")

    if not isinstance(tasks, list):
        return HttpResponseBadRequest("Field 'tasks' must be a list")

    scored_tasks = analyze_tasks_algo(tasks, strategy=strategy)
    top_three = scored_tasks[:3]

    response = JsonResponse(
        {
            "strategy": strategy,
            "suggested": top_three,
        }
    )
    response["Access-Control-Allow-Origin"] = "*"
    return response
