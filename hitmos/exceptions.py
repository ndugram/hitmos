class HitmosError(Exception):
    """Base exception."""


class AuthError(HitmosError):
    """Invalid or missing API key."""


class NetworkError(HitmosError):
    """Network connectivity issue."""


class APIError(HitmosError):
    """API returned an error."""


class RateLimitError(APIError):
    """Rate limit exceeded."""


class ConfigError(HitmosError):
    """Configuration error."""
