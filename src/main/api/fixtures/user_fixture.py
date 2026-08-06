import pytest
from src.main.api.models.create_user_request import CreateUserRequest
from src.main.api.generators.model_generator import RandomModelGenerotor

@pytest.fixture
def create_user_request(api_manager):
    user_request = RandomModelGenerotor.generate(CreateUserRequest)
    api_manager.admin_steps.create_user(user_request)
    return user_request
