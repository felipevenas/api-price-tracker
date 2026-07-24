# Exceptions de domínio — desacoplam a camada de domínio do FastAPI.
# As rotas traduzem essas exceções para HTTPException.


class DomainError(Exception):
    """Exceção base para todos os erros de domínio."""
    pass


class NotFoundError(DomainError):
    """Recurso não encontrado."""
    def __init__(self, message: str = "Recurso não encontrado."):
        super().__init__(message)


class ConflictError(DomainError):
    """Conflito de dados (ex: email já cadastrado)."""
    def __init__(self, message: str = "Conflito de dados."):
        super().__init__(message)


class UnprocessableError(DomainError):
    """Dados encontrados mas não processáveis (ex: preço zerado)."""
    def __init__(self, message: str = "Dados não processáveis."):
        super().__init__(message)


class ServiceUnavailableError(DomainError):
    """Serviço externo indisponível (ex: API sem credenciais)."""
    def __init__(self, message: str = "Serviço externo indisponível."):
        super().__init__(message)
