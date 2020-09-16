from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask


def task():
    """ Function for test purposes. """
    print("Scheduler is alive!")


schedule = BackgroundScheduler(daemon=True)
schedule.add_job(task, 'interval', seconds=10)
schedule.start()

app = Flask(__name__)


@app.route("/home")
def home():
    return "Welcome Home :) !"


if __name__ == "__main__":
    app.run()
