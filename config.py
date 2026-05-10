# Display window (minutes from midnight)
DISPLAY_START_MIN = 5 * 60   # 5:00 AM
DISPLAY_END_MIN   = 21 * 60  # 9:00 PM
SLOT_MINUTES      = 30

# Beede Aquatics Center lap pool hours by weekday (0=Mon … 6=Sun).
# Facility hours: Mon–Fri 5:30 AM–9:00 PM, Sat–Sun 7:00 AM–6:00 PM.
# Lap pool closes 15 minutes before facility closing.
# Each entry is (open_minutes, close_minutes) from midnight, or None if closed.
POOL_HOURS = {
    0: (5*60+30, 20*60+45),  # Monday:    5:30 AM – 8:45 PM
    1: (5*60+30, 20*60+45),  # Tuesday:   5:30 AM – 8:45 PM
    2: (5*60+30, 20*60+45),  # Wednesday: 5:30 AM – 8:45 PM
    3: (5*60+30, 20*60+45),  # Thursday:  5:30 AM – 8:45 PM
    4: (5*60+30, 20*60+45),  # Friday:    5:30 AM – 8:45 PM
    5: (7*60,    17*60+45),  # Saturday:  7:00 AM – 5:45 PM
    6: (7*60,    17*60+45),  # Sunday:    7:00 AM – 5:45 PM
}
