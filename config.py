# Display window (minutes from midnight)
DISPLAY_START_MIN = 5 * 60   # 5:00 AM
DISPLAY_END_MIN   = 21 * 60  # 9:00 PM
SLOT_MINUTES      = 30

# Beede Aquatics Center lap pool hours by weekday (0=Mon … 6=Sun).
# Each entry is (open_minutes, close_minutes) from midnight, or None if closed.
# Verify / update at: https://concordrec.myrec.com  or call the Beede Center.
POOL_HOURS = {
    0: (5*60+30, 21*60),   # Monday:    5:30 AM – 9:00 PM
    1: (5*60+30, 21*60),   # Tuesday:   5:30 AM – 9:00 PM
    2: (5*60+30, 21*60),   # Wednesday: 5:30 AM – 9:00 PM
    3: (5*60+30, 21*60),   # Thursday:  5:30 AM – 9:00 PM
    4: (5*60+30, 21*60),   # Friday:    5:30 AM – 9:00 PM
    5: (7*60,    17*60),   # Saturday:  7:00 AM – 5:00 PM
    6: (8*60,    14*60),   # Sunday:    8:00 AM – 2:00 PM
}
