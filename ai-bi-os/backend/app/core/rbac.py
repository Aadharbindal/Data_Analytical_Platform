from enum import Enum

class Role(str, Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"

def check_permission(user_role: Role, required_role: Role) -> bool:
    role_hierarchy = {
        Role.ADMIN: 3,
        Role.ANALYST: 2,
        Role.VIEWER: 1
    }
    return role_hierarchy.get(user_role, 0) >= role_hierarchy.get(required_role, 0)
