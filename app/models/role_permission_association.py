from sqlalchemy import Table, Column, ForeignKey

from app.models import BaseModel

role_permission_association_table = Table(
    'role_permission_association',
    BaseModel.metadata,
    Column('role_id', ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', ForeignKey('permissions.id'), primary_key=True)
)
