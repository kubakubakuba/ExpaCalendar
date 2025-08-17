import pickle
import os.path
from datetime import datetime, timedelta
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from collections import defaultdict
import os
from datetime import datetime
from fpdf import FPDF
import qrcode
import locale
from PIL import Image
from random import randint
from twilight import Twilight

class ExpaCalendar:
	def __init__(self, config):
		self.CONFIG = config
		self.OUT_FOLDER = self.CONFIG.output_folder
		self.CALENDAR_LINK = self.CONFIG.calendar_shortlink
		self.QR_SIZE = self.CONFIG.qr_size
		self.SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
		
		self.creds = None
		self.service = None
		self.calendar_dict = defaultdict(list)
		self.rick = False if randint(0, 100) > self.CONFIG.rick_probability else True

		if os.path.exists('token.pickle'):
			with open('token.pickle', 'rb') as token:
				self.creds = pickle.load(token)

		if not self.creds or not self.creds.valid:

			if self.creds and self.creds.expired and self.creds.refresh_token:
				self.creds.refresh(Request())
			else:
				flow = InstalledAppFlow.from_client_secrets_file('credentials.json', self.SCOPES)
				self.creds = flow.run_local_server(port=0)
				
			with open('token.pickle', 'wb') as token:
				pickle.dump(self.creds, token)

		self.service = build('calendar', 'v3', credentials=self.creds)

	def get_calendar_events(self, start_date = None, end_date=None) -> dict:
		'''Returns a dictionary with dates as keys and events as values'''
		if not start_date or not end_date:
			#current_year = datetime.now().year
			sd = self.CONFIG.start_date.split(';')
			ed = self.CONFIG.end_date.split(';')
			start_date = f"{sd[0]}-{sd[1]}-{sd[2]}T00:00:00Z"
			end_date = f"{ed[0]}-{ed[1]}-{ed[2]}T23:59:59Z"

		#check date format
		assert datetime.strptime(start_date, '%Y-%m-%dT%H:%M:%SZ')
		assert datetime.strptime(end_date, '%Y-%m-%dT%H:%M:%SZ')

		calendar_id = self.CONFIG.calendar_link
		events_result = self.service.events().list(calendarId=calendar_id, timeMin=start_date, timeMax=end_date, singleEvents=True, orderBy='startTime').execute()
		events = events_result.get('items', [])

		if not events:
			print('No upcoming events found.')

		for event in events:
			start = event['start'].get('dateTime', event['start'].get('date'))
			end = event['end'].get('dateTime', event['end'].get('date'))

			if event.get('summary'):
				date = datetime.fromisoformat(start)
				key_date = date.strftime("%d.%m. %Y")
				
				location = event.get('location', '')
				description = event.get('description', '')

				event_data = dict(
					end = datetime.fromisoformat(end).strftime("%H:%M"),
					summary=event['summary'],
					location=location,
					description=description
				)

				event = tuple([date.strftime("%H:%M"), event_data])
				
				self.calendar_dict[key_date].append(event)

		return self.calendar_dict

	def day_en_to_cz(self, day: str) -> str:
		'''Converts a day name from English to Czech'''
		
		days = {
			"Monday": "Pondělí",
			"Tuesday": "Úterý",
			"Wednesday": "Středa",
			"Thursday": "Čtvrtek",
			"Friday": "Pátek",
			"Saturday": "Sobota",
			"Sunday": "Neděle"
		}

		return days.get(day, day)
	
	def moon_phase_en_to_cz(self, phase: str) -> str:
		'''Converts a moon phase from English to Czech'''
		
		phases = {
			"NEW_MOON": "Nov",
			"WAXING_CRESCENT": "Dorůstající srpek",
			"FIRST_QUARTER": "První čtvrť",
			"WAXING_GIBBOUS": "Dorůstající Měsíc",
			"FULL_MOON": "Úplněk",
			"WANING_GIBBOUS": "Couvající Měsíc",
			"LAST_QUARTER": "Poslední čtvrť",
			"WANING_CRESCENT": "Couvající srpek"
		}

		return phases.get(phase, phase)
	
	def get_moon_phase_image(self, phase: float) -> str:
		folder = "img/"
		images = [f"{folder}moon{i}.png" for i in range(17)]

		ranges = [(0, 1), (1, 7.4), (7.4, 14.8), (14.8, 22.1), (22.1, 29.5),
				(29.5, 36.9), (36.9, 43.2), (43.2, 56.3), (56.3, 62.6), (62.6, 68.9),
				(68.9, 75.2), (75.2, 81.5), (81.5, 87.8), (87.8, 94.1), (94.1, 100)]
		
		z = zip(images, ranges)

		img = [i for i, (l, u) in z if l <= phase < u]

		return img[0]
	
	def generate_timestamps(self, date: str, pdf) -> None:
		current_x, current_y = pdf.get_x(), pdf.get_y() #get cursor location

		twilight = Twilight(self.CONFIG.lat, self.CONFIG.lng, date, self.CONFIG.tmz).data

		date_tomorrow = datetime.strptime(date, '%d.%m. %Y') + timedelta(days=1)
		date_tomorrow = date_tomorrow.strftime('%d.%m. %Y')
		twilight_tomorrow = Twilight(self.CONFIG.lat, self.CONFIG.lng, date_tomorrow, self.CONFIG.tmz).data
		
		 # Set font for moon phase text
		pdf.set_font("Roboto-Regular", size=10)

		# Overlay moon phase text at a specific position
		pdf.set_xy(145, 40)
		pdf.cell(0, 0, txt=f'{self.moon_phase_en_to_cz(twilight["moon_phase"])}, col: {int(twilight["colongitude"])}°', ln=False, align="L")

		pdf.set_xy(134, 40)

		pdf.set_font('DejaVu', '', 14)
		pdf.cell(0, 0, txt=twilight["moon_phase_emoji"], ln=False, align="L")

		pdf.set_font("Roboto-Regular", size=10)

		sunrise_dt = datetime.fromisoformat(twilight_tomorrow["sunrise"]).strftime('%H:%M:%S')
		sunset_dt = datetime.fromisoformat(twilight["sunset"]).strftime('%H:%M:%S')
		moonrise_dt = datetime.fromisoformat(twilight["moonrise"]).strftime('%H:%M:%S') if twilight["moonrise"] != '-' else datetime.fromisoformat(twilight_tomorrow["moonrise"]).strftime('%H:%M:%S')
		moonset_dt = datetime.fromisoformat(twilight["moonset"]).strftime('%H:%M:%S') if twilight["moonset"] != '-' else datetime.fromisoformat(twilight_tomorrow["moonset"]).strftime('%H:%M:%S')
		
		golden_begin_time_m = datetime.fromisoformat(twilight["golden_hour_morning"]["start"]).time().strftime('%H:%M:%S')
		golden_end_time_m = datetime.fromisoformat(twilight["golden_hour_morning"]["end"]).time().strftime('%H:%M:%S')
		golden_begin_time_e = datetime.fromisoformat(twilight["golden_hour_evening"]["start"]).time().strftime('%H:%M:%S')
		golden_end_time_e = datetime.fromisoformat(twilight["golden_hour_evening"]["end"]).time().strftime('%H:%M:%S')

		#'astronomical_twilight_begin': sunrise_sunset_data['astronomical_twilight_begin'],
		#	'astronomical_twilight_end':

		astron_from = datetime.fromisoformat(twilight["astronomical_twilight_begin"]).time().strftime('%H:%M:%S')
		astron_to = datetime.fromisoformat(twilight["astronomical_twilight_end"]).time().strftime('%H:%M:%S')

		pdf.set_xy(145, 50)
		pdf.cell(0, 0, txt=f'{moonrise_dt}', ln=False, align="L")

		pdf.set_xy(175, 50)
		pdf.cell(0, 0, txt=f'{moonset_dt}', ln=False, align="L")

		pdf.set_xy(145, 60)
		pdf.cell(0, 0, txt=f'{sunset_dt}', ln=False, align="L")

		pdf.set_xy(175, 60)
		pdf.cell(0, 0, txt=f'{sunrise_dt}', ln=False, align="L")

		pdf.set_xy(145, 70)
		pdf.cell(0, 0, txt=f'Astron. noc: {astron_to} - {astron_from}', ln=False, align="L")

		#pdf.set_xy(145, 80)
		#pdf.cell(0, 0, txt=f'Zlatá hodinka: {golden_begin_time_m} - {golden_end_time_m}', ln=True, align="L")

		#pdf.set_xy(145, 85)
		#pdf.cell(0, 0, txt=f'                          {golden_begin_time_e} - {golden_end_time_e}', ln=False, align="L")

		#moon_img = self.get_moon_phase_image(twilight["moon_phase_num"])

		#pdf.image(moon_img, 135, 36.5, 6, 6)

		pdf.image("img/moonrise.png", 135, 46.5, 6, 6)

		pdf.image("img/moonset.png", 165, 46.5, 6, 6)

		pdf.image("img/sunset.png", 135, 56.5, 6, 6)

		pdf.image("img/sunrise.png", 165, 56.5, 6, 6)

		pdf.image("img/telescope.png", 135, 66.5, 6, 6)
		
		#pdf.image("img/sun.png", 135, 76.5, 6, 6)

		pdf.set_xy(current_x, current_y) #reset cursor

	def generate_pdf(self, calendar_dict):
		'''Generates a PDF file for each date in the calendar_dict'''
		if not os.path.exists(self.OUT_FOLDER):
			os.makedirs(self.OUT_FOLDER)

		qr = qrcode.QRCode(
				version=1,
				error_correction=qrcode.constants.ERROR_CORRECT_L,
				box_size=10,
				border=4,
			)

		qr.add_data(self.CALENDAR_LINK if not self.rick else "https://www.youtube.com/watch?v=dQw4w9WgXcQ")
		qr.make(fit=True)
		qr_image = qr.make_image(fill_color="black", back_color="white")

		qr_image_path = "qr_code.png"  # Save the QR code as an image temporarily
		qr_image.save(qr_image_path)

		for date_str, events in calendar_dict.items():
			# Create a new PDF instance
			pdf = FPDF()
			pdf.add_page()

			available_space = pdf.h - pdf.get_y() - 50 # Leave some space for the QR code
			
			# add unicode font
			pdf.add_font('Roboto-Bold', '', 'fonts/Roboto-Bold.ttf', uni=True)
			pdf.add_font('Roboto-Regular', '', 'fonts/Roboto-Regular.ttf', uni=True)
			pdf.add_font('Roboto-ThinItalic', '', 'fonts/Roboto-ThinItalic.ttf', uni=True)
			pdf.add_font('Righteous', '', 'fonts/Righteous.ttf', uni=True)
			pdf.add_font('NotoEmoji', '', 'fonts/NotoEmoji-Regular.ttf', uni=True)
			pdf.add_font('SegoeUI', '', 'fonts/segoe-ui.ttf', uni=True)
			pdf.add_font('DejaVu', '', 'fonts/DejaVuSans.ttf', uni=True)
			
			self.generate_timestamps(date_str, pdf)

			pdf.set_font('Roboto-Regular', '', 12)

			pdf.set_font("Righteous", size=22)
			pdf.cell(200, 10, txt=f"{self.CONFIG.name} {datetime.now().strftime('%Y')} - denní program", ln=True, align="L")

			pdf.line(10, pdf.get_y() + 1, 200, pdf.get_y() + 1) # +1 because of the image covering the line

			pdf.set_font("Roboto-Regular", size=14)

			date_name = datetime.strptime(date_str, '%d.%m. %Y').strftime('%A')
			date_name = self.day_en_to_cz(date_name) if self.CONFIG.lang == 'cz' else date_name
			pdf.cell(190, 10, txt=f"Program na {date_str[:-5]} ({date_name})", ln=True, align="R")

			
			# Loop through events
			pdf.set_font("Roboto-Regular", size=12)
			for time, event in events:
				indent = 0
				event_data = event

				pdf.set_font("Roboto-Bold", "", 12)
				
				if event_data['summary'].startswith("@sluzba:") or event_data['summary'].startswith("@služba:"):
					cx, cy = pdf.get_x(), pdf.get_y() #get cursor location
					pdf.image("img/people.png", 135, 76.5, 6, 6)
					pdf.set_xy(145, 80)
					pdf.set_font("Roboto-Regular", "", 10)
					pdf.cell(0, 0, txt="Služba:", border=0)

					groups = event_data['summary'].split(":")[1].split(",")

					pos = 80
					pdf.set_font("Righteous", "", 10)
					for g in groups:
						pdf.set_xy(158, pos)
						pdf.cell(0, 0, txt=g, border=0)
						pdf.ln()
						pos += 6

					pdf.set_xy(cx, cy) #reset cursor
					continue

				skip = ["Východ Slunce", "Západ Slunce", "Východ Měsíce", "Západ Měsíce", "@služba", "@sluzba"]
				
				summary = event_data['summary']
				if summary in skip or (summary.startswith("# ") and summary[2:] in skip) or (summary.startswith("#") and summary[1:] in skip):
					continue

				pdf.set_font("Righteous", "", 12)
				pdf.cell(0, 6, txt=event_data['summary'], border=0, ln=True)

				if event_data['end'] == time:
					pdf.set_font("Roboto-Regular", "", 10)
					pdf.cell(20, 6, txt=time, border=0)
				else:
					pdf.set_font("Roboto-Regular", "", 10)
					pdf.cell(20, 6, txt=time + " - " + event_data['end'], border=0)

				if event_data['location'] != "":
					indent += 1
					pdf.set_font("Roboto-Regular", "", 10)
					pdf.cell(10)  # Indent for location
					pdf.cell(0, 6, txt=event_data['location'], border=0, ln=True)
				
				if event_data['description'] != "":
					indent += 1
					pdf.set_font("Roboto-Regular", "", 8)
					pdf.cell(10)  # Indent for description
					#remove empty newlines
					event_data['description'] = "\n".join(line for line in event_data['description'].splitlines() if line.strip())
					pdf.multi_cell(0, 5, txt=event_data['description'], border=0, ln=True)
					#add empty line after description
					pdf.cell(0, 2.5, txt="", border=0, ln=True)
				
				if indent < 1:
					pdf.multi_cell(0, 8, txt="", border=0, ln=True)
			
				# Add QR code to the right side
				qr_code_x = pdf.w - 50
				qr_code_y = pdf.h - 65
					
				pdf.image(qr_image_path, qr_code_x, qr_code_y, self.QR_SIZE, self.QR_SIZE)

				pdf.image("img/expa_inv.png", pdf.w - 20, 0, 20, 20)
				
				year = datetime.now().strftime('%Y')
				pdf.set_font("Righteous", size=12)
				expa_year = f"{year[2]}.{year[3]}"
				pdf.text(pdf.w - 6.7 - pdf.get_string_width(expa_year), 14, expa_year)

				# Add a line above the footer
				pdf.line(10, pdf.h - 20, pdf.w - 10, pdf.h - 20)

				# Add footer text
				pdf.set_font("Roboto-Regular", size=10)
				footer_text = f"Strana {pdf.page_no()}"
				pdf.text(pdf.w - 20 - pdf.get_string_width(footer_text) / 2, pdf.h - 14, footer_text)

				pdf.set_font("Roboto-Regular", size=8)
				pdf.text(10, pdf.h - 14, "V programu může dojít ke změnám. Aktuální verze programu je v online verzi dynamického programu.")
				
				pdf.text(10, pdf.h - 10, "V případě špatného počasí bude místo pozorování vymyšlen náhradní program. Pozorování je možné prodloužit po dohodě s vedoucím.")
			
				generated_time = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
				link_text = f"Vygenerováno {generated_time} za pomoci Generátoru programů pro Astronomickou expedici https://github.com/kubakubakuba/ExpaCalendar"

				pdf.set_font("Roboto-Regular", size=8)
				pdf.text(10, pdf.h - 6, link_text)

				pdf.text(qr_code_x + 7, qr_code_y + self.QR_SIZE, self.CALENDAR_LINK)

				# Convert date_str to a format suitable for filenames
				date_obj = datetime.strptime(date_str, '%d.%m. %Y')
				filename = date_obj.strftime('program_%Y_%m_%d') + ".pdf"
				path_to_save = os.path.join(self.OUT_FOLDER, filename)

			# Save the PDF to the specified location
			pdf.output(path_to_save)

			rick_on = "" if not self.rick else " with rick on"
			print(f"PDF {path_to_save} generated successfully! {(rick_on)}")

		os.remove(qr_image_path)  # Remove the temporary image
