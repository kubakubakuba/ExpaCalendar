# Expa Calendar Generator
Generator of pdf calendars using [Google Calendar API](https://developers.google.com/calendar/).

## Usage
Create a Google API application with access to Calendar API and create OAuth 2 credentials for it. Download credentials.json file to access this application.
The code for generating the calendar is in the ExpaCalendar.py file. The code is written in Python 3.7. You can run it using the following commands:
```python
class Config:
    def __init__(self):
        self.calendar_link = '<your full calendar link>'
        self.calendar_shortlink = '<your calendar shortlink to be displayed under the QR code>'
        self.output_folder = 'programy'
        self.qr_size = 40
        self.lang = 'cz'
        self.rick_probability = 5 # 5% chance of Rick Astley appearing in the QR code
        
from ExpaCalendar import ExpaCalendar

calendar = ExpaCalendar(Config())
events = calendar.get_calendar_events()
calendar.generate_pdf(events)
```
Don't forget to install the required packages using the following command:
```bash
pip install -r requirements.txt
```