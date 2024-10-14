import io
import os
import sqlite3 as sl
import numpy as np
import pandas as pd
from flask import Flask, redirect, render_template, request, session, url_for, send_file
from datetime import datetime
import pytz
import calendar
from JPN_data import final_df
import secrets

pd.set_option('display.max_columns', None)

app = Flask(__name__)
app.secret_key = 'your_secure_random_key'

@app.route('/', methods=['GET', 'POST'])
def home():
    # Default values for the time and date
    est = pytz.timezone('America/New_York')
    tokyo = pytz.timezone('Asia/Tokyo')
    local_time = datetime.now(est).strftime('%A %B %d, %Y %I:%M %p')
    japan_time = datetime.now(tokyo).strftime('%A %B %d, %Y %I:%M %p')
    time_difference_str = f"Japan is 13 hours ahead of New York."

    start_date = session.get('start_date', None)
    end_date = session.get('end_date', None)
    days_until_trip = session.get('days_until_trip', None)

    if request.method == 'POST':
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')

        # Convert date strings to datetime objects
        try:
            start_date_dt = datetime.strptime(start_date_str, '%m/%d/%Y')
            end_date_dt = datetime.strptime(end_date_str, '%m/%d/%Y')

            # Calculate the number of days until the start date
            today = datetime.now(est).date()
            days_until_trip = (start_date_dt.date() - today).days

            start_date = start_date_dt.strftime('%A %B %d, %Y')
            end_date = end_date_dt.strftime('%A %B %d, %Y')

            # Store in session
            session['start_date'] = start_date
            session['end_date'] = end_date
            session['days_until_trip'] = days_until_trip

        except ValueError:
            # Handle invalid date format
            start_date = end_date = "Invalid date format. Please use mm/dd/yyyy."

    return render_template(
        'home.html',
        local_time=local_time,
        japan_time=japan_time,
        time_difference_str=time_difference_str,
        start_date=start_date,
        end_date=end_date,
        days_until_trip=days_until_trip
    )

def get_calendar_starting_sunday(year, month, start_date=None, end_date=None):
    cal = calendar.Calendar(firstweekday=6)  # Week starts on Sunday
    month_days = cal.monthdayscalendar(year, month)

    # Initialize empty calendar list
    calendar_list = []

    # Helper function to determine the highlight class
    def get_class_name(day):
        if start_date and end_date:
            date = datetime(year, month, day)
            if date == start_date:
                return 'highlight-start'
            elif date == end_date:
                return 'highlight-end'
            elif start_date < date < end_date:
                return 'highlight-range'
        return ''

    for week in month_days:
        week_list = []
        for day in week:
            if day == 0:
                week_list.append((day, ''))
            else:
                class_name = get_class_name(day)
                print(f"Day: {day}, Class: {class_name}")
                week_list.append((day, class_name))

        print(week_list)
        calendar_list.append(week_list)

    return calendar_list

@app.route('/calendar_page')
def calendar_page():
    # Get start_date and end_date from session
    start_date_str = session.get('start_date')
    end_date_str = session.get('end_date')

    # Default to current date if no dates are provided
    now = datetime.now()
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%A %B %d, %Y')
            month = start_date.month
            year = start_date.year
        except ValueError:
            # Handle invalid date format
            start_date = None
            month = now.month
            year = now.year
    else:
        start_date = None
        month = now.month
        year = now.year

    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%A %B %d, %Y')
        except ValueError:
            # Handle invalid date format
            end_date = None
    else:
        end_date = None

    # Generate the calendar with weeks starting on Sunday
    cal = get_calendar_starting_sunday(year, month, start_date, end_date)

    # Get month and year names
    month_name = calendar.month_name[month]
    year_name = str(year)

    return render_template('calendar_page.html', cal=cal, month_name=month_name, year_name=year_name)

@app.route('/page2')
def page2():
    return render_template('page2.html')

####### CREATE PHOTO ALBUM PAGE !!!!!!!!

@app.route('/map')
def map_page():
    locations = final_df[['name', 'latitude', 'longitude']].values.tolist()
    return render_template('map.html', api_key='ENTER_WHEN_READY', locations=locations)


if __name__ == '__main__':
    app.run(debug=True)