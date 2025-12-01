from fastapi.params import Depends

from app.repository.user_repo import UserRepository
from app.service.user_service import UserService


def get_user_repository() -> UserRepository:
    return UserRepository()


def get_user_service(user_repo: UserRepository = Depends(get_user_repository)) -> UserService:
    return UserService(user_repo=user_repo)
