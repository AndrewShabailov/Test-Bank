import pytest

from src.main.api.classes.api_manager import ApiManager
from src.main.api.models.login_user_request import LoginUserRequest


@pytest.mark.api
class TestUserLogin:
    def test_login_admin(self, api_manager):
        user_manager = ApiManager(created_obj, username=user.username, password=user.password)
        user_manager.admin_steps.get_users()  # → 403
        login_user_request = LoginUserRequest(username="admin", password="123456")
        response = api_manager.admin_steps.login_user(login_user_request)

        assert login_user_request.username == response.user.username
        assert response.user.role == "ROLE_ADMIN"


    def test_login_user(self, api_manager, create_user_request):
        response = api_manager.admin_steps.login_user(create_user_request)

        assert create_user_request.username == response.user.username
        assert response.user.role == "ROLE_USER"
