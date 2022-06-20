"""Sample API Client."""
import logging
import asyncio
import socket
from typing import Optional
import aiohttp
import async_timeout
from .poled_interface import poled_interface

TIMEOUT = 10
_LOGGER: logging.Logger = logging.getLogger(__package__)

class PoLEDApiClient:
    def __init__(self, userID: int) -> None:

        # Initialize PoLED interface
        self._pli = poled_interface()
        self._user = None

        # Search for the PoLED gateway, retry 5 times
        for retry in range(5):
            #g = self._pli.discover_gateway()
            #result = self._pli.connect(next(g, [[None]][0][0]))
            result = self._pli.connect("192.168.88.99")
            if result == False:                
                continue
            else:
                self._pli.get_users()
                self._pli.get_status(self._pli.users[userID])
                self._user = self._pli.users[userID]            

        if self._user is None:
            _LOGGER.error("PoLED gateway not detected")
        
        
    def sync_get_data(self):
        self._pli.get_status(self._user)
        [self._pli.get_blind_position(i) for i in range(12)]

    def set_status(self, group):
        self._pli.set_status(self._user, group)

    def set_blind_position(self, blind):
        self._pli.set_blind_position(blind)

    def stop_blind(self, blind):
        self._pli.stop_blind(blind)
    