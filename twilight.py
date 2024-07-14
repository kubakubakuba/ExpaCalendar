import requests
from datetime import datetime, timedelta
import ephem
import pytz

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
		return dt.isoformat()

	def get_moon_phase(self, date):
		date = datetime.strptime(date, "%d.%m. %Y")
		moon = ephem.Moon(date)
		phase = moon.phase

		return phase

	def get_moon_phase_txt(self, date):
		"""Calculate the moon phase using pyephem."""
		date = datetime.strptime(date, "%d.%m. %Y")
		moon = ephem.Moon(date)
		phase = moon.phase

		phases = [
			(0, 1, "New Moon"),
			(1, 7.4, "Waxing Crescent"),
			(7.4, 14.8, "First Quarter"),
			(14.8, 22.1, "Waxing Gibbous"),
			(22.1, 29.5, "Full Moon"),
			(29.5, 36.9, "Waning Gibbous"),
			(36.9, 43.2, "Last Quarter"),
			(43.2, 56.3, "Waning Crescent"),
			(56.3, 62.6, "Last Quarter"),
			(62.6, 68.9, "Waning Gibbous"),
			(68.9, 75.2, "Full Moon"),
			(75.2, 81.5, "Waxing Gibbous"),
			(81.5, 87.8, "First Quarter"),
			(87.8, 94.1, "Waxing Crescent"),
			(94.1, 100, "New Moon")
		]

		# Iterate over phases
		phase_name = [name for s, e, name in phases if s <= phase < e]

		return phase_name[0]

	def fetch_astronomical_data(self):
		"""Fetches astronomical data for the given location and date."""
		# API endpoints
		self.formatted_date = datetime.strptime(self.date, "%d.%m. %Y").strftime("%Y-%m-%d")

		sunrise_sunset_url = f'https://api.sunrise-sunset.org/json?lat={self.lat}&lng={self.lng}&date={self.formatted_date}&formatted=0'

		sunrise_sunset_response = requests.get(sunrise_sunset_url)
		sunrise_sunset_data = sunrise_sunset_response.json()['results']

		moon_phase = self.get_moon_phase_txt(str(self.date))
		moon_phase_num = self.get_moon_phase(str(self.date))

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
			'moon_phase_num': moon_phase_num,
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
		
		print(data)
		return data

if __name__ == "__main__":
	# Test data
	lat = 40.7128
	lng = -74.0060
	date = '3.7. 2023'
	timezone = 'Europe/Prague'
	
	astro_data = Twilight(lat, lng, date, timezone)
	print(astro_data.data)