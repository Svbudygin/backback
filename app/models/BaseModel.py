from sqlalchemy.orm import DeclarativeBase


class UpdateMixin:
    """
    Add a simple update() method to instances that accepts
    a dictionary of updates.
    """

    def update_if_not_none(self, values: dict):
        for k, v in values.items():
            if k == "second_number":
                setattr(self, k, v)
            elif v is not None:
                setattr(self, k, v)


class BaseModel(DeclarativeBase, UpdateMixin):
    pass
