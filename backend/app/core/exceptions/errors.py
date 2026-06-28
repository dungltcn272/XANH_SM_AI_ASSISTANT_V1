from __future__ import annotations


class AppError(Exception):
    status_code = 400
    code = "app_error"

    def __init__(self, message: str, *, status_code: int | None = None, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code or self.status_code
        self.code = code or self.code


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"
