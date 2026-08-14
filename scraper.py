
import re
import requests
from pathlib import Path
from datetime import datetime

from bs4 import BeautifulSoup
from ics import Calendar, Event


from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTfEQzPCJt-7dMhkirXClwGe0mIIcWF5HHN6Wle0sUN8K-tkIwnMnsTt9g31XKcsSDrC8DEQiu-URd3/pubhtml?gid=0&single=true"







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

    options = Options()

    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)

    try:

        driver.get(URL)

        time.sleep(10)

        iframe = driver.find_element(
            By.ID,
            "pageswitcher-content"
        )

        driver.switch_to.frame(iframe)

        time.sleep(10)

        html = driver.page_source

        print("IFRAME HTML LENGTH:", len(html))

        return html

    finally:
        driver.quit()














def dump_rows(soup):

    table = soup.find("table", class_="waffle")
    

    rows = table.find_all("tr")

    for i, row in enumerate(rows[:30]):
        cells = row.find_all(["td", "th"])

        values = [
            c.get_text(" ", strip=True)
            for c in cells
        ]

        print(i, values)

from datetime import datetime
import re


def parse_date(date_text):

    # "Monday 8/3" -> date object
    month, day = date_text.split()[-1].split("/")

    month = int(month)
    day = int(day)

    year = 2026

    # handle September dates
    if month == 9:
        year = 2026

    return datetime(year, month, day)


def parse_practice(practice_text):

    # "6-7:30pm CHS"
    parts = practice_text.rsplit(" ", 1)

    time_part = parts[0]
    location = parts[1]

    return {
        "time": time_part,
        "location": location
    }

from datetime import datetime
import re


def parse_date(date_text):
    month, day = date_text.split()[-1].split("/")

    return datetime(
        year=2026,
        month=int(month),
        day=int(day)
    )


def parse_practice(practice_text):

    practice_text = practice_text.strip()

    location = practice_text.split()[-1]

    time_part = practice_text.rsplit(" ", 1)[0]

    return {
        "time": time_part,
        "location": location
    }




def parse_time_range(time_text):

    time_text = time_text.replace(" ", "")

    start_raw, end_raw = time_text.split("-")

    return {
        "start": start_raw,
        "end": end_raw
        }
def main():

    html = fetch_page()

    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table", class_="waffle")

    rows = []

    for tr in table.find_all("tr"):
        values = [
            c.get_text(" ", strip=True)
            for c in tr.find_all(["td", "th"])
        ]
        rows.append(values)
    GROUPS = {"S1", "S2", "S3", "Blue", "AG1", "AG2"}

    events = []

    current_dates = None

    for i, row in enumerate(rows):

        if len(row) > 3 and "Monday" in " ".join(row):
            current_dates = row[3:10]
            continue

        team = row[1] if len(row) > 1 else ""

        if team in GROUPS:

            if team in {"S1", "S2", "Blue"}:
                schedule_row = rows[i + 1]
            else:
                schedule_row = row

            times = schedule_row[3:10]

            for date_text, time_text in zip(current_dates, times):

                if not time_text:
                    continue

                if "OFF" in time_text.upper():
                    continue
                

                event_date = parse_date(date_text)

                practice_info = parse_practice(time_text)

                


                parsed_time = parse_time_range(
                    practice_info["time"]
                    )

               event_record = {
                    "team": team,
                    "date": event_date,
                    "start": parsed_time["start"],
                    "end": parsed_time["end"],
                    "location": practice_info["location"]
                    }

                print(event_record)
                

                
                events.append({
                    "team": team,
                    "date": date_text,
                    "practice": time_text
                    })

    #print("TOTAL EVENTS:", len(events))
    #for e in events[:10]:
        #print(e)
    
    #print("TOTAL EVENTS:", len(events))
    #for e in events[:5]:
        #print(e)
       



    #dump_rows(soup)

    with open("calendars/page.txt", "w") as f:
        f.write(html)


if __name__ == "__main__":
    main()
