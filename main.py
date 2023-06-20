from app import app, Session
import schedule
import time
from config import load_config

# load config
config = load_config("config.yaml")
interval = config["interval"]
session = Session()


def job():
    try:
        app(session, config)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    job()  # test
    schedule.every(interval).minutes.do(job)
    while True:
        schedule.run_pending()
        time.sleep(1)
