import re
import time
from datetime import datetime, date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

import requests
from bs4 import BeautifulSoup

FACILITY_ID = 14698
BASE_URL = "https://concordrec.myrec.com/info/calendar/mobile.aspx"

# Individual lap lane area IDs
LANE_IDS = {
    1: 14854, 2: 14855, 3: 14856, 4: 14857,
    5: 14858, 6: 14859, 7: 14860, 8: 14861,
}

# Multi-lane block-booking areas → which individual lanes they affect
TEAM_USE_IDS = {
    14880: [1, 2, 3],           # Lap Lanes 1-3 (Team Use)
    14867: list(range(1, 9)),   # Lap Lanes 1-8 (Team Use)
    14864: [3, 4],              # Lap Lanes 3-4 (Team Use)
    14862: list(range(3, 9)),   # Lap Lanes 3-8 (Team Use)
    14863: list(range(4, 9)),   # Lap Lanes 4-8 (Team Use)
    14883: list(range(5, 9)),   # Lap Lanes 5-8 (Team Use)
    14881: [6, 7, 8],           # Lap Lanes 6-8 (Team Use)
    14866: list(range(1, 9)),   # Full Pool Closure
}

_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": "Mozilla/5.0 (BeededPoolSchedule/1.0)"})

_cache: dict = {}
_CACHE_TTL = 3600  # seconds


def parse_time_range(text: str) -> tuple[Optional[int], Optional[int]]:
    """'4:00 PM - 5:30 PM' → (960, 1050) minutes from midnight."""
    cleaned = re.sub(r"[\s\xa0]+", " ", text).strip()
    m = re.match(
        r"(\d{1,2}:\d{2}\s*[APap][Mm])\s*[-–]\s*(\d{1,2}:\d{2}\s*[APap][Mm])",
        cleaned,
    )
    if not m:
        return None, None

    def to_min(t: str) -> Optional[int]:
        t = t.strip().upper()
        for fmt in ("%I:%M %p", "%I:%M%p"):
            try:
                dt = datetime.strptime(t, fmt)
                return dt.hour * 60 + dt.minute
            except ValueError:
                continue
        return None

    return to_min(m.group(1)), to_min(m.group(2))


def _fetch_area_week(area_id: int, week_start: date) -> dict[str, list]:
    """Fetch one area page; return {date_iso: [{start, end, name}]}."""
    week_end = week_start + timedelta(days=6)
    url = (
        f"{BASE_URL}?FacilityID={FACILITY_ID}"
        f"&AreaID={area_id}"
        f"&StartDate={week_start.strftime('%m/%d/%Y')}"
    )
    resp = _SESSION.get(url, timeout=15)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    result: dict[str, list] = {}

    for table in soup.find_all("table", class_="styled"):
        title_row = table.find("tr", class_="trTitle")
        if not title_row:
            continue
        date_text = title_row.get_text(" ", strip=True)
        try:
            page_date = datetime.strptime(date_text.strip(), "%A %B %d, %Y").date()
        except ValueError:
            continue
        if not (week_start <= page_date <= week_end):
            continue

        events = []
        for row in table.find_all("tr", class_="row"):
            tds = row.find_all("td")
            if len(tds) < 2:
                continue
            start_min, end_min = parse_time_range(tds[0].get_text(" ", strip=True))
            if start_min is None:
                continue
            events.append({
                "start": start_min,
                "end": end_min,
                "name": tds[1].get_text(strip=True),
            })

        if events:
            result[page_date.isoformat()] = events

    return result


def get_week_schedule(week_start: date) -> dict:
    """
    Return {date_iso: {'lane_1': [events], ..., 'lane_8': [events]}}
    Results are cached for one hour.
    """
    cache_key = week_start.isoformat()
    if cache_key in _cache:
        data, ts = _cache[cache_key]
        if time.time() - ts < _CACHE_TTL:
            return data

    # Initialise empty structure
    schedule: dict = {}
    for i in range(7):
        d = (week_start + timedelta(days=i)).isoformat()
        schedule[d] = {f"lane_{n}": [] for n in range(1, 9)}

    # Build: area_id → list of lane keys to populate
    tasks: dict[int, list[str]] = {}
    for lane_num, area_id in LANE_IDS.items():
        tasks[area_id] = [f"lane_{lane_num}"]
    for area_id, lanes in TEAM_USE_IDS.items():
        tasks[area_id] = [f"lane_{n}" for n in lanes]

    def fetch_and_distribute(area_id: int, lane_keys: list[str]):
        events_by_date = _fetch_area_week(area_id, week_start)
        out = []
        for date_str, events in events_by_date.items():
            for key in lane_keys:
                for ev in events:
                    out.append((date_str, key, ev))
        return out

    with ThreadPoolExecutor(max_workers=12) as executor:
        futures = {
            executor.submit(fetch_and_distribute, aid, keys): aid
            for aid, keys in tasks.items()
        }
        for future in as_completed(futures):
            try:
                for date_str, lane_key, event in future.result():
                    if date_str in schedule and lane_key in schedule[date_str]:
                        schedule[date_str][lane_key].append(event)
            except Exception as exc:
                print(f"[scraper] area {futures[future]} failed: {exc}")

    _cache[cache_key] = (schedule, time.time())
    return schedule
