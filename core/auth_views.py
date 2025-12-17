import os

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken


User = get_user_model()


@api_view(["GET"])
@permission_classes([AllowAny])
def demo_login(request):
    username = os.environ.get("DEMO_USER_USERNAME", "demo")
    password = os.environ.get("DEMO_USER_PASSWORD", "demo123!")
    email = os.environ.get("DEMO_USER_EMAIL", "demo@example.com")

    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            "email": email,
            "is_staff": False,
            "is_superuser": False,
        },
    )
    if created:
        user.set_password(password)
        user.save()

    try:
        ip = request.META.get("HTTP_X_FORWARDED_FOR", "").split(",")[0].strip() or request.META.get(
            "REMOTE_ADDR", "unknown"
        )
    except Exception:
        ip = "unknown"
    key = f"demo_login:{ip}"
    cnt = cache.get(key)
    if cnt is None:
        cache.set(key, 1, timeout=3600)
    else:
        if cnt >= 30:
            return HttpResponse(
                "<h1>Too Many Requests</h1><p>Please try again later..</p>",
                status=429,
            )
        try:
            cache.incr(key)
        except Exception:
            cache.set(key, cnt + 1, timeout=3600)

    refresh = RefreshToken.for_user(user)
    access = str(refresh.access_token)
    refresh_token = str(refresh)

    redirect_to = request.GET.get("redirect", "/")

    html = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta name="robots" content="noindex, nofollow" />
    <title>Signing you in…</title>
    <style>
      body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; display:flex; align-items:center; justify-content:center; min-height:100vh; background:#f8fafc; color:#0f172a; }}
      .card {{ background:#fff; padding:24px 28px; border-radius:12px; box-shadow: 0 10px 25px rgba(2,6,23,0.08); max-width: 420px; text-align:center; }}
      .spinner {{ width: 32px; height: 32px; border: 3px solid #e2e8f0; border-top-color: #6366f1; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 10px; }}
      @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    </style>
  </head>
  <body>
    <div class="card">
      <div class="spinner"></div>
      <h1>Entrando no modo demo…</h1>
      <p>Você será redirecionado em instantes.</p>
    </div>
    <script>
      try {{
        localStorage.setItem('access_token', {access!r});
        localStorage.setItem('refresh_token', {refresh_token!r});
        localStorage.removeItem('user');
      }} catch (e) {{
        console.error('Failed to store tokens', e);
      }}
      window.location.replace({redirect_to!r});
    </script>
  </body>
</html>"""

    return HttpResponse(html, content_type="text/html")
