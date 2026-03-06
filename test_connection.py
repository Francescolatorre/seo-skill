from google.oauth2 import service_account
from googleapiclient.discovery import build

SERVICE_ACCOUNT_FILE = 'oleks-488616-4fe597a49127.json'
SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']

# Authentifizierung
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

# Service erstellen
service = build('searchconsole', 'v1', credentials=credentials)

# Test 1: Verfuegbare Properties auflisten
print("=== Verbindungstest Google Search Console API ===\n")
print("Service Account:", credentials.service_account_email)
print()

try:
    site_list = service.sites().list().execute()
    entries = site_list.get('siteEntry', [])

    if entries:
        print(f"Gefundene Properties: {len(entries)}\n")
        for site in entries:
            print(f"  URL: {site['siteUrl']}")
            print(f"  Berechtigung: {site['permissionLevel']}")
            print()
    else:
        print("Keine Properties gefunden.")
        print("Hast du den Service Account in der Search Console als Nutzer hinzugefuegt?")
        print(f"  -> Fuege diese E-Mail hinzu: {credentials.service_account_email}")

    print("Verbindung erfolgreich!")

except Exception as e:
    print(f"Fehler: {e}")
