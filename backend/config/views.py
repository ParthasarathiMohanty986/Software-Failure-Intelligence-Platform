from django.conf import settings
from django.http import FileResponse, JsonResponse, HttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET


@require_GET
def health(request):
    return JsonResponse({"status": "ok"})


@require_GET
@ensure_csrf_cookie
def frontend(request):
    index = settings.FRONTEND_DIST / "index.html"
    if not index.exists():
        return HttpResponse("Frontend build missing. Use the Vite development server locally.", status=503)
    response = FileResponse(index.open("rb"), content_type="text/html")
    response["Cache-Control"] = "no-cache"
    return response
