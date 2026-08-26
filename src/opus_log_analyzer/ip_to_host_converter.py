"""Turning a client IP address into a host name for the report.

Three strategies, chosen by command-line flag: do not look up at all, look up
through the resolver every time, or look up through the resolver and remember
the answer in a `shelve` cache between runs. All three memoize within a single
run, because a log holds many entries per host.
"""
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
from typing import Any


class IpToHostConverter(metaclass=abc.ABCMeta):
    """
    This class is the abstract superclass of any class that has a method 'convert' that converts an ip address
    to a host name.
    """
    RESULT_TYPE = Callable[[IPv4Address], str | None]

    @staticmethod
    def get_ip_to_host_converter(uses_reverse_dns: bool, dns_cache: bool,
                                 **_args: Any) -> IpToHostConverter:
        """Return the converter the command-line arguments select.

        Parameters:
            uses_reverse_dns: Whether to resolve at all.
            dns_cache: Whether to keep resolved names in a shelf between runs.
                Only consulted when `uses_reverse_dns` is set.
            **_args: The rest of the parsed arguments, ignored. The caller
                passes the whole argument namespace.

        Returns:
            A `NullIpToHostConverter` when reverse DNS is off, a
            `ShelvedIPToHostConverter` on the cache at `.logs/reverse-dns` when
            caching is on, and a `NormalIpToHostConverter` otherwise. The shelf
            path is relative to the working directory.
        """
        if not uses_reverse_dns:
            return NullIpToHostConverter()
        elif dns_cache:
            return ShelvedIPToHostConverter(".logs/reverse-dns")
        else:
            return NormalIpToHostConverter()

    def __init__(self) -> None:
        """Start with an empty within-run memo."""
        self._convert_cache: dict[IPv4Address, str | None] = {}

    def convert(self, ip: IPv4Address) -> str | None:
        """Return the host name for an address, memoized for this run.

        Parameters:
            ip: The address to resolve.

        Returns:
            The host name, or None where the subclass could not supply one. A
            None result is memoized too, so a failed lookup is not retried.
        """
        if ip in self._convert_cache:
            return self._convert_cache[ip]
        result = self._convert(ip)
        self._convert_cache[ip] = result
        return result

    @abc.abstractmethod
    def _convert(self, ip: IPv4Address) -> str | None:
        """Resolve one address, without the memo.

        Parameters:
            ip: The address to resolve.

        Returns:
            The host name, or None if this strategy cannot supply one.
        """
        raise Exception()


class NullIpToHostConverter(IpToHostConverter):
    """An IpToHostConverter that just doesn't even bother trying."""

    def _convert(self, ip: IPv4Address) -> str | None:
        """Return None for every address, so the report shows raw addresses."""
        return None


class NormalIpToHostConverter(IpToHostConverter):
    """An IpToHostConverter that calls gethostbyaddr to attempt to parse its value"""

    def _convert(self, ip: IPv4Address) -> str | None:
        """Resolve one address through the system resolver.

        Parameters:
            ip: The address to resolve.

        Returns:
            The primary host name, or None if the resolver raised `OSError`,
            which covers both "no such record" and the resolver being
            unreachable.
        """
        try:
            name, _, _ = socket.gethostbyaddr(str(ip))
            return name
        except OSError:
            return None


class ShelvedIPToHostConverter(NormalIpToHostConverter):
    """A NormalIpToHostConverter that remembers answers between runs.

    Each cached answer carries an expiry 25 to 30 days out. Expired entries are
    purged when the cache is opened, and the counts are printed at exit.
    """

    _database: shelve.Shelf[tuple[str | None, datetime.datetime]]
    _cached: int
    _created: int
    _expired: int

    def __init__(self, file_name: str) -> None:
        """Open the cache, purge what has expired, and arrange to close it.

        Parameters:
            file_name: Path to the shelf, resolved against the working
                directory.
        """
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
        """Resolve one address, consulting and updating the shelf.

        Parameters:
            ip: The address to resolve.

        Returns:
            The cached name if the shelf holds an unexpired entry, otherwise
            whatever the resolver says, which is then cached -- including a None
            result, so an address that does not resolve is not retried for
            weeks.
        """
        value: tuple[str | None, datetime.datetime] | None = self._database.get(str(ip))
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
        """Delete every entry whose expiry has passed.

        Returns:
            How many entries were deleted. The count is also printed.
        """
        now = datetime.datetime.now()
        expired_keys = [key for key, (_, expiration) in self._database.items() if expiration < now]
        print(f"There are {len(expired_keys)} expired keys")
        for key in expired_keys:
            del self._database[key]
        return len(expired_keys)

    def __close(self) -> None:
        """Close the shelf at exit and print the run's cache statistics.

        Raises:
            ValueError: If the cache is empty, because the oldest expiry is a
                `min` with no default. See issue #1452.
        """
        oldest = min(expiration for (_, expiration) in self._database.values())
        self._database.close()
        print(f"IP Cache: Created {self._created}; Expired {self._expired}; Cached {self._cached}; oldest {oldest}.")

    def __testing_update_expiration(self, days: float) -> None:
        """Move every entry's expiry earlier, to exercise the purge by hand.

        Parameters:
            days: How many days earlier to move each expiry.
        """
        delta = datetime.timedelta(days=days)
        values = [(key, (value, expiration - delta)) for key, (value, expiration) in self._database.items()]
        self._database.update(values)
