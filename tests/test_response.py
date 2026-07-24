from app.core.response import success_response, error_response
from app.core.config import get_settings


def test_success_response():
    data = {"id": 1, "name": "Test Product"}
    message = "Busca realizada com sucesso"
    
    response = success_response(data=data, message=message)
    
    assert response["status"] == "success"
    assert response["message"] == message
    assert response["data"] == data


def test_success_response_default_message():
    response = success_response()
    
    assert response["status"] == "success"
    assert response["message"] == "Operação realizada com sucesso"
    assert response["data"] is None


def test_error_response_development(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "ENV", "development")
    
    message = "Erro ao buscar produto"
    details = "Product ID not found in database"
    
    response = error_response(message=message, details=details)
    
    assert response["status"] == "error"
    assert response["message"] == message
    assert response["details"] == details


def test_error_response_production(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "ENV", "production")
    
    message = "Erro interno no servidor"
    details = "Detailed stack trace that should not be visible"
    
    response = error_response(message=message, details=details)
    
    assert response["status"] == "error"
    assert response["message"] == message
    assert response["details"] is None
