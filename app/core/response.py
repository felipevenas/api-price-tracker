from app.core.config import get_settings


def success_response(data=None, message="Operação realizada com sucesso"):
    return {"status": "success", "message": message, "data": data}


def error_response(message="Ocorreu um erro", details=None):
    settings = get_settings()
    if details is not None and getattr(settings, "ENV", "development") == "production":
        details = None
    return {"status": "error", "message": message, "details": details}
