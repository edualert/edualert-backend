from rest_framework.throttling import ScopedRateThrottle


class PasswordViewsScopedRateThrottle(ScopedRateThrottle):
    def allow_request(self, request, view):
        setattr(view, self.scope_attr, 'password-views')
        return super().allow_request(request, view)
