import os
import datetime
from typing import Dict, List, Optional, Sequence, Type, Union

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build

# API FUNCTIONS
scopes = [
    'https://www.googleapis.com/auth/calendar',
    'openid'
]


def get_creds(scopes: Sequence[str], data_folder: str = 'data',
              show_auth_prompt: bool = True, reuse_creds: bool = True) -> Type[Credentials]:
    '''Get/create user credentials in given folder with specified scopes.
    Args:
        scopes: The scopes listed in the OAuth consent screen.
        data_folder: The folder containing client_secret.json and to store credentials in.
        show_auth_prompt: Whether or not to show the user the authourization link in the console.
        reuse_creds: Whether or not to use credentials from previous runs.

    Returns:
        The credentials stored or created.
    '''
    creds: Optional[Type[Credentials]] = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if reuse_creds and os.path.exists(data_folder+'\\token.json'):
        creds = Credentials.from_authorized_user_file(
            data_folder+'\\token.json', scopes)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                data_folder+'\\client_secret.json', scopes)
            if show_auth_prompt:
                creds = flow.run_local_server(port=0)
            else:
                creds = flow.run_local_server(
                    port=0, authorization_prompt_message='')
        # Save the credentials for the next run
        with open(data_folder+'\\token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


# service will be built only once per run
service = None


def get_service(reuse_creds: bool = True) -> Resource:
    '''Construct or return a service for interacting with the Calendar v3 API
    Args:
        reuse_creds: Whether or not to use credentials from previous runs.

    Returns:
        A Resource object that can interact with the Calendar v3 API
    '''
    global service, scopes
    if service is None:
        credentials: Credentials = get_creds(
            scopes, data_folder='data', show_auth_prompt=False, reuse_creds=reuse_creds)
        service = build('calendar', 'v3', credentials=credentials)
    return service


def get_calendar_list(ids=False) -> Resource:
    '''Get a calendar list's items with the first 100 calendars.

    Returns:
        A list of calendarListEntrys.
    '''
    service = get_service()
    # Default maxResults = 100 which is sufficient
    calendar_list = service.calendarList().list().execute()['items']
    if ids:
        calendar_list = [calendar['id'] for calendar in calendar_list]
    return calendar_list


def get_calendar_from_name(calendar_name: str) -> Optional[Dict]:
    '''Get the calendar associated with a given calendar name.
    Args:
        calendar_name: The name of the calendar.

    Returns:
        The calendar associated with the calendar name.
    '''
    service = get_service()
    calendars = get_calendar_list()
    for calendar in calendars:
        if calendar['summary'] == calendar_name:
            calendar_id = calendar['id']
            calendar = service.calendars().get(calendarId=calendar_id).execute()
            return calendar


def get_user_info(credentials):
    user_info_service = build('oauth2', 'v2', credentials=credentials)
    user_info = user_info_service.userinfo().get().execute()
    return user_info

today = datetime.datetime.combine(datetime.date.today(), datetime.time()).astimezone()
midnight = today + datetime.timedelta(days=1)
def moveZoomEvents():
    service = get_service()
    events = service.events()

    primary_calendar_id = service.calendars().get(calendarId="primary").execute()["id"]
    calendars = get_calendar_list(ids=True)
    new_events = []
    for calendar_id in calendars:
        if calendar_id != primary_calendar_id:
            calendar_events = events.list(
                calendarId=calendar_id,
                timeMin=today.isoformat(),
                timeMax=midnight.isoformat()
            ).execute()['items']
            for event in calendar_events:
                    if 'zoom' in event['description']:
                        new_events.append(event['summary'])
                        events.patch(calendarId=calendar_id, eventId=event['id'], body={
                            'summary': event['summary'].split(']')[1]
                        }).execute()
                        events.move(calendarId=calendar_id, eventId=event['id'], destination='primary').execute()
    return new_events

if __name__ == '__main__':
    moveZoomEvents()