import logging

from amplitude_python_sdk.common.exceptions import AmplitudeAPIException
from amplitude_python_sdk.v2.clients.event_client import EventAPIClient
from amplitude_python_sdk.v2.models.event import Event
from amplitude_python_sdk.v2.models.event.options import EventAPIOptions

from concurrent.futures import ThreadPoolExecutor

import config

executor = ThreadPoolExecutor()
client = EventAPIClient(config.settings.AMPLITUDE_APIKEY)


def def_event_api_client_amplitude(telegram_id: int, event_type: str, event_properties: dict):
    try:
        events = [
            Event(user_id=telegram_id,
                  event_type=event_type,
                  event_properties=event_properties
                  )
        ]
        client.upload(events=events,
                      options=EventAPIOptions(min_id_length=1),
                      )
        print(event_type)
    except AmplitudeAPIException:
        logging.exception('Failed to log event to Amplitude')
        print('Failed to log event to Amplitude')


def def_event_api_client(telegram_id: int, event_type: str, event_properties: dict):
    executor.submit(def_event_api_client_amplitude, telegram_id, event_type, event_properties)


