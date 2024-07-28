import requests
from datetime import datetime, timedelta
import ephem
import pytz
import pylunar

class Twilight:
	def __init__(self, lat, lng, date=None, timezone='UTC'):
		self.lat = lat
		self.lng = lng
		self.timezone = pytz.timezone(timezone)
		self.date = date if date else datetime.now().date()
		self.data = self.fetch_astronomical_data()
	
	def parse_time(self, time_str):
		"""Parse the time string to a datetime object."""
		dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
		return dt.astimezone(self.timezone)

	def format_time(self, dt):
		"""Format the datetime object to a string."""
		return dt.isoformat() if dt != '-' else '-'
	
	def convert_to_dms(self, degrees):
		"""Convert decimal degrees to degrees, minutes, and seconds."""
		d = int(degrees)
		m = int((degrees - d) * 60)
		s = (degrees - d - m / 60) * 3600
		return d, m, s

	def get_moon_data(self, date):
		date = datetime.strptime(date, "%d.%m. %Y")
		moon = pylunar.MoonInfo(self.convert_to_dms(self.lat), self.convert_to_dms(self.lng))
		moon.update((date.year, date.month, date.day, 0, 0, 0))
		
		moontimes = moon.rise_set_times(self.timezone.zone)
		moonrise = '-'
		moonset = '-'

		#print(moontimes)

		for event, time_tuple in moontimes:
			if len(time_tuple) != 6:
				#fix does not rise or set
				continue

			if event == 'rise':
				moonrise = datetime(*time_tuple)
			elif event == 'set':
				moonset = datetime(*time_tuple)

		colongitude = moon.colong()
		moon_phase = moon.phase_name()
		moon_emoji = moon.phase_emoji()

		return moonrise, moonset, colongitude, moon_phase, moon_emoji

	def fetch_astronomical_data(self):
		"""Fetches astronomical data for the given location and date."""
		self.formatted_date = datetime.strptime(self.date, "%d.%m. %Y").strftime("%Y-%m-%d")

		sunrise_sunset_url = f'https://api.sunrise-sunset.org/json?lat={self.lat}&lng={self.lng}&date={self.formatted_date}&formatted=0'

		sunrise_sunset_response = requests.get(sunrise_sunset_url)
		sunrise_sunset_data = sunrise_sunset_response.json()['results']

		moonrise, moonset, colongitude, moon_phase, moon_phase_emoji = self.get_moon_data(str(self.date))

		sunrise = self.parse_time(sunrise_sunset_data['sunrise'])
		sunset = self.parse_time(sunrise_sunset_data['sunset'])
		civil_twilight_begin = self.parse_time(sunrise_sunset_data['civil_twilight_begin'])
		civil_twilight_end = self.parse_time(sunrise_sunset_data['civil_twilight_end'])
		nautical_twilight_begin = self.parse_time(sunrise_sunset_data['nautical_twilight_begin'])
		nautical_twilight_end = self.parse_time(sunrise_sunset_data['nautical_twilight_end'])
		astronomical_twilight_begin = self.parse_time(sunrise_sunset_data['astronomical_twilight_begin'])
		astronomical_twilight_end = self.parse_time(sunrise_sunset_data['astronomical_twilight_end'])

		golden_hour_morning_start = sunrise
		golden_hour_morning_end = sunrise + timedelta(hours=1)
		golden_hour_evening_start = sunset - timedelta(hours=1)
		golden_hour_evening_end = sunset

		blue_hour_morning_start = civil_twilight_begin - timedelta(minutes=30)
		blue_hour_morning_end = civil_twilight_begin
		blue_hour_evening_start = civil_twilight_end
		blue_hour_evening_end = civil_twilight_end + timedelta(minutes=30)

		data = {
			'sunrise': self.format_time(sunrise),
			'sunset': self.format_time(sunset),
			'solar_noon': self.format_time(self.parse_time(sunrise_sunset_data['solar_noon'])),
			'day_length': sunrise_sunset_data['day_length'],
			'civil_twilight_begin': self.format_time(civil_twilight_begin),
			'civil_twilight_end': self.format_time(civil_twilight_end),
			'nautical_twilight_begin': self.format_time(nautical_twilight_begin),
			'nautical_twilight_end': self.format_time(nautical_twilight_end),
			'astronomical_twilight_begin': self.format_time(astronomical_twilight_begin),
			'astronomical_twilight_end': self.format_time(astronomical_twilight_end),
			'moon_phase': moon_phase,
			'moon_phase_emoji': moon_phase_emoji,
			'moonrise': self.format_time(moonrise),
			'moonset': self.format_time(moonset),
			'colongitude': colongitude,
			'golden_hour_morning': {
				'start': self.format_time(golden_hour_morning_start),
				'end': self.format_time(golden_hour_morning_end)
			},
			'golden_hour_evening': {
				'start': self.format_time(golden_hour_evening_start),
				'end': self.format_time(golden_hour_evening_end)
			},
			'blue_hour_morning': {
				'start': self.format_time(blue_hour_morning_start),
				'end': self.format_time(blue_hour_morning_end)
			},
			'blue_hour_evening': {
				'start': self.format_time(blue_hour_evening_start),
				'end': self.format_time(blue_hour_evening_end)
			}
		}

		#print(data)
		return data

if __name__ == "__main__":
	# Test data
	lat = 40.7128
	lng = -74.0060
	date = '17.7. 2023'
	timezone = 'Europe/Prague'
	
	astro_data = Twilight(lat, lng, date, timezone)
	print(astro_data.data)
