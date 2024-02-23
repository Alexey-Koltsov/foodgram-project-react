from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Проверка: безопасный запрос или запрос произведен автором."""

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or obj.author == request.user
        )


class IsOwner(permissions.BasePermission):
    """Проверка: произведен ли запрос владельцем."""

    def has_object_permission(self, request, view, obj):
        return (obj.user == request.user)
