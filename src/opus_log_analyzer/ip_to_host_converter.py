from __future__ import annotations

import abc
import atexit
import datetime

# Imported for the self-written DNS cache; see the shelve.open below.
import shelve  # nosec B403
import socket
from collections.abc import Callable
from ipaddress import IPv4Address
from random import uniform


class IpToHostConverter(metaclass=abc.ABCMeta):
    """
    This class is the abstract superclass of any class that has a method 'convert' that converts an ip address
    to a host name.
    """
    RESULT_TYPE = Callable[[IPv4Address], str | None]

    @staticmethod
    def get_ip_to_host_converter(uses_reverse_dns: bool, dns_cache: bool, **_args) -> IpToHostConverter:
        """
        Returns the appropriate IpToHostConvert, given the arguments.
        """
        if not uses_reverse_dns:
            return NullIpToHostConverter()
        elif dns_cache:
            return ShelvedIPToHostConverter(".logs/reverse-dns")
        else:
            return NormalIpToHostConverter()

    def __init__(self) -> None:
        self._convert_cache: dict[IPv4Address, str | None] = {}

    def convert(self, ip: IPv4Address) -> str | None:
        if ip in self._convert_cache:
            return self._convert_cache[ip]
        result = self._convert(ip)
        self._convert_cache[ip] = result
        return result

    @abc.abstractmethod
    def _convert(self, ip: IPv4Address) -> str | None:
        raise Exception()


class NullIpToHostConverter(IpToHostConverter):
    """An IpToHostConverter that just doesn't even bother trying."""
    def _convert(self, ip: IPv4Address) -> str | None:
        return None


class NormalIpToHostConverter(IpToHostConverter):
    """An IpToHostConverter that calls gethostbyaddr to attempt to parse its value"""
    def _convert(self, ip: IPv4Address) -> str | None:
        try:
            name, _, _ = socket.gethostbyaddr(str(ip))
            return name
        except OSError:
            return None


class ShelvedIPToHostConverter(NormalIpToHostConverter):
    _database: shelve.Shelf
    _cached: int
    _created: int
    _expired: int

    def __init__(self, file_name: str):
        super().__init__()
        # Long-lived persistent shelf: kept open for the object's lifetime and
        # closed via the atexit handler below, so a context manager does not fit.
        # A reverse-DNS cache this process wrote itself, under the hidden
        # --xxdns-cache flag. The input is never attacker-supplied.
        self._database = shelve.open(file_name)  # noqa: SIM115  # nosec B301
        self._expired = self.__purge_old_database_entries()
        self._cached = self._created = 0
        atexit.register(self.__close)

    def _convert(self, ip: IPv4Address) -> str | None:
        value: tuple[str | None, datetime.timedelta] | None = self._database.get(str(ip))
        if value:
            name, _timeout = value
            self._cached += 1
            return name
        self._created += 1
        name = super()._convert(ip)
        # Jitter that spreads DNS-cache expiry over a few days so the whole
        # cache does not lapse at once. Not a secret.
        expiration = datetime.datetime.now() + datetime.timedelta(days=uniform(25.0, 30.0))  # nosec B311
        self._database[str(ip)] = (name, expiration)
        return name

    def __purge_old_database_entries(self) -> int:
        now = datetime.datetime.now()
        expired_keys = [key for key, (_, expiration) in self._database.items() if expiration < now]
        print(f"There are {len(expired_keys)} expired keys")
        for key in expired_keys:
            del self._database[key]
        return len(expired_keys)

    def __close(self) -> None:
        oldest = min(expiration for (_, expiration) in self._database.values())
        self._database.close()
        print(f"IP Cache: Created {self._created}; Expired {self._expired}; Cached {self._cached}; oldest {oldest}.")

    def __testing_update_expiration(self, days):
        delta = datetime.timedelta(days=days)
        values = [(key, (value, expiration - delta)) for key, (value, expiration) in self._database.items()]
        self._database.update(values)
