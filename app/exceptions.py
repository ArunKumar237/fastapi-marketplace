from fastapi import status


class AppException(Exception):
    status_code: int

    def __init__(self, detail: str, error_code: str):
        self.detail = detail
        self.error_code = error_code
        super().__init__(detail)


class NotFoundException(AppException):
    status_code = status.HTTP_404_NOT_FOUND


class BadRequestException(AppException):
    status_code = status.HTTP_400_BAD_REQUEST


class UnauthorizedException(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED


class ForbiddenException(AppException):
    status_code = status.HTTP_403_FORBIDDEN


class ConflictException(AppException):
    status_code = status.HTTP_409_CONFLICT