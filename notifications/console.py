import logging

# Настройка логирования
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

def notify(message: str, level: str = 'info') -> None:
    if message is None:
        message = 'None'
    try:
        if level.upper() == 'INFO':
            logger.info(f'[PA:INFO] {message}')
        elif level.upper() == 'WARNING':
            logger.warning(f'[PA:WARNING] {message}')
        elif level.upper() == 'ERROR':
            logger.error(f'[PA:ERROR] {message}')
        else:
            logger.error(f'[PA:UNKNOWN] {message}')
    except Exception as e:
        logger.error(f'Ошибка при отправке уведомления: {e}')
