import datetime
from django.conf import settings
from django.shortcuts import redirect

class SessionTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            last_activity = request.session.get('last_activity')
            now = datetime.datetime.now()

            if last_activity:
                last_activity_time = datetime.datetime.strptime(last_activity, "%Y-%m-%d %H:%M:%S")
                elapsed_time = (now - last_activity_time).total_seconds()

                # Si han pasado más de 10 minutos, cerrar la sesión
                if elapsed_time > settings.SESSION_COOKIE_AGE:
                    from django.contrib.auth import logout
                    logout(request)
                    return redirect('/')

            # Actualizar el tiempo de última actividad
            request.session['last_activity'] = now.strftime("%Y-%m-%d %H:%M:%S")

        response = self.get_response(request)
        return response