"""
ASSDA Swim Calendar Generator

Pipeline:
1. Download published Google Sheet
2. Parse schedule table
3. Extract team practices
4. Convert to datetime events
5. Generate:
   - S1.ics
   - S2.ics
   - S3.ics
   - Blue.ics
   - AG1.ics
   - AG2.ics
   - gmsc_schedule.ics

Last verified: August 2026
"""

import re
from pathlib import Path
from datetime import datetime

from bs4 import BeautifulSoup
from ics import Calendar, Event
from collections import defaultdict

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

#URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTfEQzPCJt-7dMhkirXClwGe0mIIcWF5HHN6Wle0sUN8K-tkIwnMnsTt9g31XKcsSDrC8DEQiu-URd3/pubhtml?gid=0&single=true"

URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTfEQzPCJt-7dMhkirXClwGe0mIIcWF5HHN6Wle0sUN8K-tkIwnMnsTt9g31XKcsSDrC8DEQiu-URd3/pubhtml?gid=0&single=true"





OUTPUT_DIR = Path("calendars")
OUTPUT_DIR.mkdir(exist_ok=True)




def parse_time_range(time_text):

    time_text = time_text.replace(" ", "").lower()

    start_raw, end_raw = time_text.split("-")

    # inherit am/pm from end
    if not start_raw.endswith(("am", "pm")):

        if end_raw.endswith("am"):
            start_raw += "am"

        elif end_raw.endswith("pm"):
            start_raw += "pm"

    # add minutes if missing
    if ":" not in start_raw:
        start_raw = start_raw.replace("am", ":00am").replace("pm", ":00pm")

    if ":" not in end_raw:
        end_raw = end_raw.replace("am", ":00am").replace("pm", ":00pm")

    start_dt = datetime.strptime(start_raw, "%I:%M%p")
    end_dt = datetime.strptime(end_raw, "%I:%M%p")

    return {
        "start": start_dt.strftime("%H:%M"),
        "end": end_dt.strftime("%H:%M")
    }
















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









def to_24hr(time_str):
    return datetime.strptime(time_str, "%I:%M%p").strftime("%H:%M")





def build_datetimes(date_text, start_time, end_time):

    date_obj = parse_date(date_text)

    start_hour, start_minute = map(int, start_time.split(":"))
    end_hour, end_minute = map(int, end_time.split(":"))

    start_dt = date_obj.replace(
        hour=start_hour,
        minute=start_minute
    )

    end_dt = date_obj.replace(
        hour=end_hour,
        minute=end_minute
    )

    return start_dt, end_dt
    
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
                

                

                practice_info = parse_practice(time_text)

                
                parsed_time = parse_time_range(
                    practice_info["time"]
                    )

                start_dt, end_dt = build_datetimes(
                    date_text,
                    parsed_time["start"],
                    parsed_time["end"]
                    )

                events.append({
                    "team": team,
                    "start_dt": start_dt,
                    "end_dt": end_dt,
                    "location": practice_info["location"]
                    })
                
           

                
                
               print("TOTAL EVENTS:", len(events))
               print(practice_info["time"], parsed_time)

   
        
    

   




    

    

    calendar = Calendar()

    for e in events:

        event = Event()

        event.name = f"{e['team']} Practice"

        event.begin = e["start_dt"]

        event.end = e["end_dt"]

        event.location = e["location"]

        calendar.events.add(event)

    with open("calendars/gmsc_schedule.ics", "w") as f:
        f.writelines(calendar)
    print("ICS file written")

    
    

    team_calendars = defaultdict(Calendar)

    for e in events:

        event = Event()
        event.name = f"{e['team']} Practice"
        event.begin = e["start_dt"]
        event.end = e["end_dt"]
        event.location = e["location"]

        team_calendars[e["team"]].events.add(event)

# Write one file per team
    for team, calendar in team_calendars.items():

        filename = f"calendars/{team}.ics"

        with open(filename, "w") as f:
            f.writelines(calendar)
   if team == "AG1":
       

if __name__ == "__main__":
    main()
