from src.logging_config import setup_logging
setup_logging()
from src import build_ui()

def main():
    build_ui()

if __name__ == "__main__":
    main()