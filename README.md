# Beede Pool Lane Availability

Weekly visualization of lap lane availability at the **Beede Aquatics Center**, Concord, MA.

Scrapes the live facility schedule from Concord Recreation and renders a color-coded grid:

| Color | Meaning |
|-------|---------|
| 🔵 Blue | Available for lap swimming |
| 🔴 Red  | Reserved / scheduled |
| ⬜ Gray | Pool closed |

## Run locally

```bash
pip install -r requirements.txt
python app.py
```

Then open <http://localhost:5000>

## Deploy to Railway

1. Push this repo to GitHub (public or private)
2. Go to [railway.app](https://railway.app) → **New Project → Deploy from GitHub repo**
3. Select `beede-pool-schedule`
4. Railway detects the `Procfile` and deploys automatically
5. Your live URL appears in the Railway dashboard

## Configuration

Edit **`config.py`** to adjust:

- `POOL_HOURS` — open/close times per weekday (verify against the current Beede Center schedule)
- `DISPLAY_START_MIN` / `DISPLAY_END_MIN` — time window shown on the chart

## Data source

Schedule data is scraped from:
<https://concordrec.myrec.com/info/calendar/mobile.aspx?FacilityID=14698&AreaID=0>

Results are cached in-memory for 1 hour to avoid hammering the server.
