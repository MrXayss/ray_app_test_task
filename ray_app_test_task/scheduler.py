from apscheduler.schedulers.background import BackgroundScheduler
from .cron import dump_db


def start():
    scheduler = BackgroundScheduler()
    scheduler.add_job(dump_db, 'interval', hours=5)
    scheduler.start()