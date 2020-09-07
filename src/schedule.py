import sched
from datetime import datetime


def update_series():
    pass


def execute():
    s = sched.scheduler()
    dt = datetime.today()
    s.enterabs(dt, 0, update_series())
    s.run()
