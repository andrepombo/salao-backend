from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json

@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """
    Simple health check endpoint for frontend connection testing
    """
    return JsonResponse({
        'status': 'healthy',
        'message': 'Salão backend is running successfully',
        'version': '1.0.0',
        'timestamp': '2025-08-03T11:22:34-03:00'
    })
