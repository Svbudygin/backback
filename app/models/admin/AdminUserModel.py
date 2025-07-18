from app.models import UserModel


class AdminUserModel(UserModel):
    class Config:
        from_attributes = True
