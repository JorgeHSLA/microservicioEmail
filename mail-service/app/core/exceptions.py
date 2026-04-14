class EmailSendError(Exception):
    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.original_error = original_error


class InvalidEmailPayloadError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
