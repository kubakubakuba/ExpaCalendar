import pickle
import os.path
from datetime import datetime
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

	def get_calendar_events(self, start_date=None, end_date=None):
		'''Returns a dictionary with dates as keys and events as values'''
		if not start_date or not end_date:
			current_year = datetime.now().year
			start_date = f"{current_year}-01-01T00:00:00Z"
			end_date = f"{current_year}-12-31T23:59:59Z"

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

	def day_en_to_cz(self, day):
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

			pdf.set_font('Roboto-Regular', '', 12)

			pdf.set_font("Roboto-Regular", size=24)
			pdf.cell(200, 10, txt=f"Astronomická expedice {datetime.now().strftime('%Y')} - denní program", ln=True, align="L")

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
					pdf.multi_cell(0, 8, txt=event_data['description'], border=0)
				
				if indent < 1:
					pdf.multi_cell(0, 8, txt="", border=0)
			
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
