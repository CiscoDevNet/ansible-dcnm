class ControllerResponseError(Exception):
    def __init__(self, message, return_code):
        self.message = message
        self.return_code = return_code
