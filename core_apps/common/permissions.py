from rest_framework import permissions
from rest_framework.views import View
from rest_framework.request import Request

class IsAccountExecutive(permissions.BasePermission):
    def has_permission(self, request:Request, view:View)-> bool:
        is_authenticated = request.user.is_authenticated
        has_role_attr = hasattr(request.user, "roles")

        return (is_authenticated, has_role_attr and request.user.roles == "account_executive")

class IsBranchManager(permissions.BasePermission):
    def has_permission(self, request:Request, view:View)-> bool:
        is_authenticated = request.user.is_authenticated
        has_role_attr = hasattr(request.user, "roles")

        return (is_authenticated, has_role_attr and request.user.roles == "branch_manager")

class IsTeller(permissions.BasePermission):
    def has_permission(self, request:Request, view:View)-> bool:
        is_authenticated = request.user.is_authenticated
        has_role_attr = hasattr(request.user, "roles")

        return (is_authenticated, has_role_attr and request.user.roles == "teller") 
