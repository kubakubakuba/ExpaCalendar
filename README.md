# Expa Calendar Generator
Generátor pdf kalendářů za pomoci [Google Calendar API](https://developers.google.com/calendar/).

## Použití
Vytvořte si Google API aplikaci s přístupem ke Calendar API a vytvořte pro ni přístup přes OAuth 2. Stáhněte si soubor credentials.json. Vytvořte si soubor config.py a vložte do něj následující kód:
```python
class Calendar:
    def __init__(self):
        self.calendar_link = '12123123123132abcd@group.calendar.google.com'
        self.calendar_shortlink = 'http://goo.gl/AaBbCc'
        self.output_folder = 'programy'
```
Upravte proměnné podle vaší preference. calendar_link je ID kalendáře, calendar_shortlink je zkrácený odkaz na kalendář, output_folder je složka, kam se budou ukládat vygenerované kalendáře.