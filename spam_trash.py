from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os.path
import pickle

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

# Spam keywords you want to filter out
SPAM_KEYWORDS = [ "CarShield", "Nexxt","Reddit","Harbor Freight","United_Healthcare","United-Healthcare","Mini Jeep","Lowe's"]

def authenticate():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

def trash_and_log_spam(service):
    query = 'in:spam'

    response = service.users().messages().list(userId='me', q=query).execute()
    messages = response.get('messages', [])

    print("Found", len(messages), "messages.") 

    print("Messages:")
    for msg in messages:
        msg_id = msg['id']
        msg_detail = service.users().messages().get(
            userId='me', id=msg_id, format='metadata', metadataHeaders=['From', 'Subject']
        ).execute()

        snippet = msg_detail.get('snippet', '')
        headers = msg_detail.get('payload', {}).get('headers', [])

        sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')

        combined_text = f"{snippet} {sender} {subject}"

        print("Checking:", combined_text[:100]) 

        if any(word.lower() in combined_text.lower() for word in SPAM_KEYWORDS):
            print(f"Trashing: {subject[:50]}... | From: {sender}")
            service.users().messages().trash(userId='me', id=msg_id).execute()
            with open("blocked_senders.txt", "a") as f:
                f.write(sender + "\n")


if __name__ == '__main__':
    service = authenticate()
    trash_and_log_spam(service)
