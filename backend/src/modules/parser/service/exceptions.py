class ParserError(Exception):
    pass


class ParserConnectionError(ParserError):
    pass


class ParserParseError(ParserError):
    pass


class ParserAuthError(ParserError):
    pass
