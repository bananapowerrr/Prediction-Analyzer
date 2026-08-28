class TutorialError(Exception):
    """Базовое исключение приложения desktop-tutorial."""


class ConfigError(TutorialError):
    """Ошибка конфигурации приложения."""


class UIError(TutorialError):
    """Ошибка пользовательского интерфейса."""


class PAError(TutorialError):
    """Базовое исключение для приложения desktop-tutorial."""
