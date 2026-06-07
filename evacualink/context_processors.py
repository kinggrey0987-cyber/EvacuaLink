from mapping.models import SystemSettings

def system_settings(request):
    """
    Injects the active SystemSettings into the context of all templates.
    """
    try:
        settings = SystemSettings.objects.first()
    except Exception:
        settings = None

    return {
        'system_settings': settings
    }
