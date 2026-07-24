import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.domain.user.schemas import UserCreate, UserUpdate
from app.domain.user.usecase import UpdateUserUseCase
from app.domain.product.schemas import ProductCreate, ProductUpdate
from app.domain.product.model import ProductMonitored
from app.domain.product.usecase import (
    CreateProductUseCase,
    ListProductsUseCase,
    GetProductUseCase,
    UpdateProductUseCase,
    DeleteProductUseCase,
    ListProductPriceHistoryUseCase,
)
from app.domain.auth.usecase import RegisterUserUseCase, AuthenticateUserUseCase
from app.domain.exceptions import NotFoundError, ConflictError


@pytest.mark.asyncio
async def test_update_user_use_case():
    repo = MagicMock()
    user_mock = MagicMock(id=uuid.uuid4(), email="old@test.com", password_hash="hash", full_name="User")
    repo.get_by_id = AsyncMock(return_value=user_mock)
    repo.save = AsyncMock(side_effect=lambda u: u)

    updated = await UpdateUserUseCase(repo).execute(user_mock.id, UserUpdate(full_name="Updated Name"))
    assert updated.full_name == "Updated Name"


@pytest.mark.asyncio
async def test_product_crud_use_cases():
    product_repo = MagicMock()
    product_mock = ProductMonitored(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        name="Smartphone",
        url="https://mercadolivre.com.br/p",
        target_price=1000.0,
        check_interval_minutes=60,
        active=True,
    )
    product_repo.create = AsyncMock(return_value=product_mock)
    product_repo.get_by_user_and_id = AsyncMock(return_value=product_mock)
    product_repo.get_by_user = AsyncMock(return_value=[product_mock])
    product_repo.save = AsyncMock(return_value=product_mock)
    product_repo.delete = AsyncMock(return_value=None)

    audit_repo = MagicMock()
    audit_repo.create = AsyncMock()

    history_repo = MagicMock()
    history_repo.get_by_product = AsyncMock(return_value=[])

    user_id = uuid.uuid4()

    # Create
    created = await CreateProductUseCase(product_repo, audit_repo).execute(
        user_id, ProductCreate(name="Smartphone", url="https://mercadolivre.com.br/p", target_price=1000.0)
    )
    assert created.name == "Smartphone"
    audit_repo.create.assert_called_once()

    # List
    listed = await ListProductsUseCase(product_repo).execute(user_id)
    assert len(listed) == 1

    # Get
    found = await GetProductUseCase(product_repo).execute(user_id, product_mock.id)
    assert found.id == product_mock.id

    # Update
    updated = await UpdateProductUseCase(product_repo, audit_repo).execute(
        user_id, product_mock.id, ProductUpdate(name="New Smartphone")
    )
    assert updated.name == "New Smartphone"

    # Delete
    await DeleteProductUseCase(product_repo, audit_repo).execute(user_id, product_mock.id)

    # History
    history = await ListProductPriceHistoryUseCase(product_repo, history_repo).execute(user_id, product_mock.id)
    assert history == []


@pytest.mark.asyncio
async def test_get_product_raises_not_found():
    product_repo = MagicMock()
    product_repo.get_by_user_and_id = AsyncMock(return_value=None)

    with pytest.raises(NotFoundError):
        await GetProductUseCase(product_repo).execute(uuid.uuid4(), uuid.uuid4())


@pytest.mark.asyncio
async def test_register_user_use_case():
    user_repo = MagicMock()
    user_repo.get_by_email = AsyncMock(return_value=None)
    user_mock = MagicMock(email="auth@test.com")
    user_repo.create = AsyncMock(return_value=user_mock)

    result = await RegisterUserUseCase(user_repo).execute(
        UserCreate(email="auth@test.com", password="password123", full_name="Auth User")
    )
    assert result.email == "auth@test.com"


@pytest.mark.asyncio
async def test_register_user_raises_conflict_on_duplicate_email():
    user_repo = MagicMock()
    user_repo.get_by_email = AsyncMock(return_value=MagicMock())  # usuário já existe

    with pytest.raises(ConflictError):
        await RegisterUserUseCase(user_repo).execute(
            UserCreate(email="dup@test.com", password="123456", full_name="Dup")
        )


def test_use_cases_can_be_instantiated_with_repositories():
    """Garante que use cases aceitam repositórios sem erro de construção."""
    mock_db = MagicMock()
    from app.domain.product.repository import ProductRepository
    from app.domain.audit_log.repository import AuditLogRepository
    from app.domain.price_history.repository import PriceHistoryRepository
    from app.domain.user.repository import UserRepository

    product_repo = ProductRepository(mock_db)
    audit_repo = AuditLogRepository(mock_db)
    history_repo = PriceHistoryRepository(mock_db)
    user_repo = UserRepository(mock_db)

    assert isinstance(CreateProductUseCase(product_repo, audit_repo), CreateProductUseCase)
    assert isinstance(ListProductsUseCase(product_repo), ListProductsUseCase)
    assert isinstance(GetProductUseCase(product_repo), GetProductUseCase)
    assert isinstance(UpdateProductUseCase(product_repo, audit_repo), UpdateProductUseCase)
    assert isinstance(DeleteProductUseCase(product_repo, audit_repo), DeleteProductUseCase)
    assert isinstance(ListProductPriceHistoryUseCase(product_repo, history_repo), ListProductPriceHistoryUseCase)
    assert isinstance(RegisterUserUseCase(user_repo), RegisterUserUseCase)
    assert isinstance(AuthenticateUserUseCase(user_repo), AuthenticateUserUseCase)
