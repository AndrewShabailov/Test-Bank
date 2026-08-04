from src.main.api.models.base_model import BaseModel


class LoginUserResponse(BaseModel):
    id: int
    username: str
    password: str
    role: str
    