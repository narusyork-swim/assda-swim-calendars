
from pathlib import Path

Path("calendars").mkdir(exist_ok=True)

with open("calendars/test.txt", "w") as f:
    f.write("GitHub Actions is working!")
