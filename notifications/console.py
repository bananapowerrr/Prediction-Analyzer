def notify(message: str, level: str = 'info') -> None:
    if message is None:
        message = 'None'
    print(f'[PA:{level.upper()}] {message}')
