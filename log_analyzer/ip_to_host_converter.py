import abc
import atexit
import datetime
import functools
import shelve
import socket
from ipaddress import IPv4Address
from random import seed, randrange, choice, uniform
from typing import Optional, Callable, Tuple


class IpToHostConverter(metaclass=abc.ABCMeta):
    """
    This class is the abstract superclass of any class that has a method 'convert' that converts an ip address
    to a host name.
    """
    RESULT_TYPE = Callable[[IPv4Address], Optional[str]]

    @staticmethod
    def get_ip_to_host_converter(uses_reverse_dns: bool, uses_local: bool, dns_cache: bool) -> 'IpToHostConverter':
        """
        Returns the appropriate IpToHostConvert, given the arguments.
        """
        if not uses_reverse_dns:
            return NullIpToHostConverter()
        elif uses_local:
            return FakeIpToHostConverter()
        elif dns_cache:
            return ShelvedIPToHostConverter(".logs/reverse-dns")
        else:
            return NormalIpToHostConverter()

    @functools.lru_cache(maxsize=None)
    def convert(self, ip: IPv4Address) -> Optional[str]:
        return self._convert(ip)

    @abc.abstractmethod
    def _convert(self, ip: IPv4Address) -> Optional[str]:
        raise Exception()


class NullIpToHostConverter(IpToHostConverter):
    """An IpToHostConverter that just doesn't even bother trying."""
    def _convert(self, ip: IPv4Address) -> Optional[str]:
        return None


class NormalIpToHostConverter(IpToHostConverter):
    """An IpToHostConverter that calls gethostbyaddr to attempt to parse its value"""
    def _convert(self, ip: IPv4Address) -> Optional[str]:
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
        self._database = shelve.open(file_name)
        self._expired = self._purge_old_database_entries()
        self._cached = self._created = 0
        atexit.register(self._close)

    def _convert(self, ip: IPv4Address) -> Optional[str]:
        value: Optional[Tuple[Optional[str], datetime.timedelta]] = self._database.get(str(ip))
        if value:
            name, _timeout = value
            self._cached += 1
            return name
        self._created += 1
        name = super()._convert(ip)
        expiration = datetime.datetime.now() + datetime.timedelta(days=uniform(25.0, 30.0))
        self._database[str(ip)] = (name, expiration)
        return name

    def _purge_old_database_entries(self) -> int:
        now = datetime.datetime.now()
        expired_keys = [key for key, (_, expiration) in self._database.items() if expiration < now]
        print(f"There are {len(expired_keys)} expired keys")
        for key in expired_keys:
            del self._database[key]
        return len(expired_keys)

    def _close(self) -> None:
        oldest = min(expiration for (_, expiration) in self._database.values())
        self._database.close()
        print(f"IP Cache: Created {self._created}; Expired {self._expired}; Cached {self._cached}; oldest {oldest}.")


class FakeIpToHostConverter(IpToHostConverter):
    """An IpToHostConverter that returns fake, but reproducible names."""
    COMPANIES = ('nasa', 'cia', 'pets', 'whitehouse', 'toysRus', 'sears', 'enron', 'pan-am', 'twa')
    ISPS = ('comcast', 'verizon', 'warner')
    TLDS = ('gov', 'mil', 'us', 'fr', 'uk', 'edu', 'es', 'eu')

    def _convert(self, ip: IPv4Address) -> Optional[str]:
        seed(str(ip))  # seemingly random, but deterministic, so we'll get the same result between runs.
        i = randrange(5)
        if i == 0:
            ip_str = str(ip).replace('.', '-')
            return f'{choice(self.ISPS)}.{ip_str}.{choice(self.TLDS)}'
        elif i == 1:
            return None
        else:
            return f'{choice(self.COMPANIES)}.{randrange(256)}.{choice(self.TLDS)}'
