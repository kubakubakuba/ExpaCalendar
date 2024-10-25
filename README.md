# Wiki link
More detailed instructions are now on my wiki page:
[ExpaCalendar wiki page](https://wiki.swpelc.eu/ExpaCalendar/)

# Expa Calendar Generator
Generator of pdf calendars using [Google Calendar API](https://developers.google.com/calendar/).

## Usage
Create a Google API application with access to Calendar API and create OAuth 2 credentials for it. Download credentials.json file to access this application.
The code for generating the calendar is in the ExpaCalendar.py file. You can create this simple configuration object that you then create the `ExpaCalendar` object with.
Note that some of these configurations are not fully utilised, and will be extended in future updates.
```python
class Config:
    def __init__(self):
        self.calendar_link = '<your full calendar link>'
        self.calendar_shortlink = '<your calendar shortlink to be displayed under the QR code>'
        self.output_folder = 'programy'
        self.name = 'Mikroexpedice' # a name to show in the header of the calendar
        self.start_date = '2024;10;25'
        self.end_date = '2024;10;28'
        self.qr_size = 40
        self.lang = 'cz'
        self.lat = 49.971980
        self.lng = 16.271130
        self.tmz = 'Europe/Prague'
        self.timezone = 'Europe/Prague'
        self.min_elevation = 10
        self.satellite_names = ['NOAA 15', 'NOAA 18', 'NOAA 19', 'METEOR-M 2', 'ISS (ZARYA)']
        self.rick_probability = 5 # 5% chance of Rick Astley appearing in the QR code
        
from ExpaCalendar import ExpaCalendar
calendar = ExpaCalendar(Config())
events = calendar.get_calendar_events()
calendar.generate_pdf(events)
```

Don't forget to install the required packages:

```bash
pip install -r requirements.txt
```
