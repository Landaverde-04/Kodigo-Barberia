from django.conf import settings


def identidad_barberia(request):
    return {"nombre_barberia": settings.NOMBRE_BARBERIA}
