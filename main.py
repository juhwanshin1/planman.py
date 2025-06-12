# GUI 실행
import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()

from ui.interface import launch_main_gui

if __name__ == "__main__":
    launch_main_gui()