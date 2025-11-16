"""Sample API Client."""
import logging

from .poled_interface import poled_interface

_LOGGER: logging.Logger = logging.getLogger(__package__)

class PoLEDApiClient:
    def __init__(self, host: str, userID: int) -> None:

        # Initialize PoLED interface
        self._pli = poled_interface()
        self._user = None
        self._host = host
        self._user_id = userID

        # Search for the PoLED gateway, retry 5 times
        for retry in range(5):
            result = self._pli.connect(host)
            if result == False:
                continue
            else:
                self._pli.get_users()
                if userID < len(self._pli.users):
                    self._pli.get_status(self._pli.users[userID])
                    self._user = self._pli.users[userID]
                break

        if self._user is None:
            _LOGGER.error("PoLED gateway not detected or invalid user ID")

    @property
    def host(self) -> str:
        """Return the host address."""
        return self._host

    @property
    def user_id(self) -> int:
        """Return the user ID."""
        return self._user_id

    def sync_get_data(self):
        self._pli.get_status(self._user)
        [self._pli.get_blind_position(i) for i in range(12)]

    def set_status(self, group):
        self._pli.set_status(self._user, group)

    def set_blind_position(self, blind):
        self._pli.set_blind_position(blind)

    def stop_blind(self, blind):
        self._pli.stop_blind(blind)
    