

import re
import requests
from pathlib import Path
from datetime import datetime

from bs4 import BeautifulSoup
from ics import Calendar, Event

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTfEQzPCJt-7dMhkirXClwGe0mIIcWF5HHN6Wle0sUN8K-tkIwnMnsTt9g31XKcsSDrC8DEQiu-URd3/pubhtml/sheet?headers=false&gid="

GROUPS = [
    "S1",
    "S2",
    "S3",
    "Blue",
    "AG1",
    "AG2",
]


OUTPUT_DIR = Path("calendars")
OUTPUT_DIR.mkdir(exist_ok=True)





def extract_text(html):

    soup = BeautifulSoup(html, "lxml")

    return soup.get_text(" ", strip=True)


def create_calendars():

    calendars = {}

    for group in GROUPS:
        calendars[group] = Calendar()

    return calendars


def parse_time_range(time_text):

    time_text = time_text.strip().lower()

    match = re.match(
        r'(\d{1,2})(?::(\d{2}))?(am|pm)?-'
        r'(\d{1,2})(?::(\d{2}))?(am|pm)',
        time_text,
    )

    if not match:
        return None

    sh, sm, sap, eh, em, eap = match.groups()

    if sap is None:
        sap = eap

    start_hour = int(sh)
    start_minute = int(sm or 0)

    end_hour = int(eh)
    end_minute = int(em or 0)

    if sap == "pm" and start_hour < 12:
        start_hour += 12

    if sap == "am" and start_hour == 12:
        start_hour = 0

    if eap == "pm" and end_hour < 12:
        end_hour += 12

    if eap == "am" and end_hour == 12:
        end_hour = 0

    return (
        start_hour,
        start_minute,
        end_hour,
        end_minute,
    )


def build_events_from_text(text):

    calendars = create_calendars()

    year = datetime.now().year

    date_matches = re.findall(
        r'(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+(\d+/\d+)',
        text
    )

    dates = []

    for _, md in date_matches:
        month, day = md.split("/")

        dates.append(
            datetime(
                year,
                int(month),
                int(day)
            )
        )

    for group in GROUPS:

        pattern = rf"{group}(.*?)(?={'|'.join(GROUPS)}|Posted Schedule|$)"

        blocks = re.findall(
            pattern,
            text,
            re.IGNORECASE,
        )

        for block in blocks:

            practices = re.findall(
                r'(\d{{1,2}}(?::\d{{2}})?(?:am|pm)?-\d{{1,2}}(?::\d{{2}})?(?:am|pm))\s+([A-Za-z]+)',
                block,
                re.IGNORECASE,
            )

            for i, (time_range, location) in enumerate(practices):

                if i >= len(dates):
                    continue

                parsed = parse_time_range(time_range)

                if not parsed:
                    continue

                sh, sm, eh, em = parsed

                practice_date = dates[i]

                begin = practice_date.replace(
                    hour=sh,
                    minute=sm,
                )

                end = practice_date.replace(
                    hour=eh,
                    minute=em,
                )

                uid = (
                    f"{group}-"
                    f"{practice_date:%Y%m%d}-"
                    f"{time_range}"
                )

                event = Event()

                event.name = f"{group} Practice"
                event.begin = begin
                event.end = end
                event.location = location
                event.uid = uid

                calendars[group].events.add(event)

    return calendars





def save_calendars(calendars):

    for group, calendar in calendars.items():

        filename = OUTPUT_DIR / f"{group}.ics"

        with open(filename, "w") as f:
            f.writelines(calendar)

        print(f"Created {filename}")





def fetch_page():

    response = requests.get(
        URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/138.0 Safari/537.36"
            )
        },
        timeout=30,
    )

    print("STATUS:", response.status_code)

    
if response.status_code != 200:
    print(response.text[:2000])
    raise Exception(
        f"HTTP {response.status_code}"
    )


    return response.text




def main():

    html = fetch_page()

    print("HTML LENGTH:", len(html))
    print(html[:1000])




    with open("calendars/page.html", "w") as f:
        f.write(html)

    text = extract_text(html)

    with open("calendars/page.txt", "w") as f:
        f.write(text)

    calendars = build_events_from_text(text)

    save_calendars(calendars)


if __name__ == "__main__":
    main()




