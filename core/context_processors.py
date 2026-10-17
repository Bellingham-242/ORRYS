from .models import SystemConfig

def global_system_config(request):
    return {
        'config': SystemConfig.get_solo()
    }