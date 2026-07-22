import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.api.deps import get_user_repository
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
    ListProductPriceHistoryUseCase
)
from app.domain.product.routes import (
    get_product_repository,
    get_audit_log_repository,
    get_price_history_repository,
    get_create_product_use_case,
    get_list_products_use_case,
    get_product_use_case,
    get_update_product_use_case,
    get_delete_product_use_case,
    get_list_price_history_use_case,
)
from app.domain.auth.usecase import RegisterUserUseCase, AuthenticateUserUseCase
from app.domain.auth.routes import get_register_user_use_case, get_authenticate_user_use_case


@pytest.mark.asyncio
async def test_user_use_cases():
    repo = MagicMock()
    user_mock = MagicMock(id=uuid.uuid4(), email="old@test.com", password_hash="hash", full_name="User")
    repo.get_by_id = AsyncMock(return_value=user_mock)
    repo.save = AsyncMock(side_effect=lambda u: u)

    update_uc = UpdateUserUseCase(repo)
    update_in = UserUpdate(full_name="Updated Name")
    updated = await update_uc.execute(user_mock.id, update_in)
    assert updated.full_name == "Updated Name"


@pytest.mark.asyncio
async def test_product_use_cases_direct_repositories():
    product_repo = MagicMock()
    product_mock = ProductMonitored(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        name="Smartphone",
        url="https://mercadolivre.com.br/p",
        target_price=1000.0,
        check_interval_minutes=60,
        active=True
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

    # Create UseCase
    create_uc = CreateProductUseCase(product_repo, audit_repo)
    p_in = ProductCreate(name="Smartphone", url="https://mercadolivre.com.br/p", target_price=1000.0)
    created = await create_uc.execute(user_id, p_in)
    assert created.name == "Smartphone"
    audit_repo.create.assert_called_once()

    # List UseCase
    list_uc = ListProductsUseCase(product_repo)
    listed = await list_uc.execute(user_id)
    assert len(listed) == 1

    # Get UseCase
    get_uc = GetProductUseCase(product_repo)
    found = await get_uc.execute(user_id, product_mock.id)
    assert found.id == product_mock.id

    # Update UseCase
    update_uc = UpdateProductUseCase(product_repo, audit_repo)
    updated_p = await update_uc.execute(user_id, product_mock.id, ProductUpdate(name="New Smartphone"))
    assert updated_p.name == "New Smartphone"

    # Delete UseCase
    delete_uc = DeleteProductUseCase(product_repo, audit_repo)
    await delete_uc.execute(user_id, product_mock.id)

    # Price History UseCase
    history_uc = ListProductPriceHistoryUseCase(product_repo, history_repo)
    res_hist = await history_uc.execute(user_id, product_mock.id)
    assert res_hist == []


@pytest.mark.asyncio
async def test_auth_use_cases_direct_repository():
    user_repo = MagicMock()
    user_repo.get_by_email = AsyncMock(return_value=None)
    user_mock = MagicMock(email="auth@test.com")
    user_repo.create = AsyncMock(return_value=user_mock)

    reg_uc = RegisterUserUseCase(user_repo)
    u_in = UserCreate(email="auth@test.com", password="password123", full_name="Auth User")
    res = await reg_uc.execute(u_in)
    assert res.email == "auth@test.com"


def test_dependency_injection_providers_direct_repositories():
    mock_db = MagicMock()
    
    user_repo = get_user_repository(mock_db)
    reg_uc = get_register_user_use_case(user_repo)
    auth_uc = get_authenticate_user_use_case(user_repo)
    assert isinstance(reg_uc, RegisterUserUseCase)
    assert isinstance(auth_uc, AuthenticateUserUseCase)

    product_repo = get_product_repository(mock_db)
    audit_repo = get_audit_log_repository(mock_db)
    history_repo = get_price_history_repository(mock_db)

    create_prod_uc = get_create_product_use_case(product_repo, audit_repo)
    list_prod_uc = get_list_products_use_case(product_repo)
    get_prod_uc = get_product_use_case(product_repo)
    update_prod_uc = get_update_product_use_case(product_repo, audit_repo)
    delete_prod_uc = get_delete_product_use_case(product_repo, audit_repo)
    list_hist_uc = get_list_price_history_use_case(product_repo, history_repo)

    assert isinstance(create_prod_uc, CreateProductUseCase)
    assert isinstance(list_prod_uc, ListProductsUseCase)
    assert isinstance(get_prod_uc, GetProductUseCase)
    assert isinstance(update_prod_uc, UpdateProductUseCase)
    assert isinstance(delete_prod_uc, DeleteProductUseCase)
    assert isinstance(list_hist_uc, ListProductPriceHistoryUseCase)
