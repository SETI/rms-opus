import abc
import functools
import socket
from ipaddress import IPv4Address
from random import seed, randrange, choice
from typing import Optional


class IpToHostConverter(metaclass=abc.ABCMeta):
    @staticmethod
    def get_ip_to_host_converter(uses_reverse_dns: bool, uses_local: bool) -> 'IpToHostConverter':
        """
        Returns the appropriate IpToHostConvert, given the arguments.
        """
        if not uses_reverse_dns:
            return NullIpToHostConverter()
        elif uses_local:
            return FakeIpToHostConverter()
        else:
            return NullIpToHostConverter()

    @classmethod
    @functools.lru_cache(maxsize=None)
    def convert(cls, ip: IPv4Address) -> Optional[str]:
        return cls._convert(ip)

    @classmethod
    @abc.abstractmethod
    def _convert(cls, ip: IPv4Address) -> Optional[str]:
        raise Exception()


class NullIpToHostConverter(IpToHostConverter):
    @classmethod
    def _convert(cls, ip: IPv4Address) -> Optional[str]:
        return None


class NormalIpToHostConverter(IpToHostConverter):
    @classmethod
    def _convert(cls, ip: IPv4Address) -> Optional[str]:
        try:
            name, _, _ = socket.gethostbyaddr(str(ip))
            return name
        except OSError:
            return None


class FakeIpToHostConverter(IpToHostConverter):
    COMPANIES = ('nasa', 'cia', 'pets', 'whitehouse', 'toysRus', 'sears', 'enron', 'pan-am', 'twa')
    ISPS = ('comcast', 'verizon', 'warner')
    TLDS = ('gov', 'mil', 'us', 'fr', 'uk', 'edu', 'es', 'eu')

    @classmethod
    def _convert(cls, ip: IPv4Address) -> Optional[str]:
        seed(str(ip))  # seemingly random, but deterministic, so we'll get the same result between runs.
        i = randrange(5)
        if i == 0:
            ip_str = str(ip).replace('.', '-')
            return f'{choice(cls.ISPS)}.{ip_str}.{choice(cls.TLDS)}'
        elif i == 1:
            return None
        else:
            return f'{choice(cls.COMPANIES)}.{randrange(256)}.{choice(cls.TLDS)}'
