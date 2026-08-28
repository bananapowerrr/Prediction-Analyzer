import os

# создано диспетчером для привязки Aider
APP_NAME = os.getenv('APP_NAME', 'prediction-analyzer')

def test_config_app():
    assert APP_NAME == 'prediction-analyzer'
