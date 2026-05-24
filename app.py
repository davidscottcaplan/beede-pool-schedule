import base64
import os
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from flask import Flask, render_template, request

from scraper import get_week_schedule
from visualizer import create_weekly_image, create_day_image

app = Flask(__name__)


def _week_start(d: date) -> date:
    """Return the Monday of the week containing d."""
    return d - timedelta(days=d.weekday())


@app.route("/")
def index():
    raw = request.args.get("week", "")
    try:
        ref = datetime.strptime(raw, "%Y-%m-%d").date() if raw else date.today()
    except ValueError:
        ref = date.today()

    week_start = _week_start(ref)
    week_end   = week_start + timedelta(days=6)

    schedule, closed_dates = get_week_schedule(week_start)
    img_bytes = create_weekly_image(schedule, week_start, closed_dates)
    img_b64   = base64.b64encode(img_bytes).decode("ascii")

    return render_template(
        "index.html",
        img_b64    = img_b64,
        view       = "week",
        week_start = week_start,
        week_end   = week_end,
        prev_week  = (week_start - timedelta(weeks=1)).isoformat(),
        next_week  = (week_start + timedelta(weeks=1)).isoformat(),
        today_week = _week_start(date.today()).isoformat(),
    )


@app.route("/today")
def today_view():
    today = datetime.now(ZoneInfo("America/New_York")).date()
    week_start = _week_start(today)

    schedule, closed_dates = get_week_schedule(week_start)
    day_sched  = schedule.get(today.isoformat(), {})

    now = datetime.now(ZoneInfo("America/New_York"))
    now_minutes = now.hour * 60 + now.minute

    img_bytes = create_day_image(day_sched, today,
                                 closed_dates=closed_dates,
                                 now_minutes=now_minutes)
    img_b64   = base64.b64encode(img_bytes).decode("ascii")

    return render_template(
        "index.html",
        img_b64    = img_b64,
        view       = "day",
        day_date   = today,
        week_start = week_start,
        week_end   = week_start + timedelta(days=6),
        prev_week  = (week_start - timedelta(weeks=1)).isoformat(),
        next_week  = (week_start + timedelta(weeks=1)).isoformat(),
        today_week = week_start.isoformat(),
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
