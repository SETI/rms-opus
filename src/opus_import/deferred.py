"""What a pool worker records in place of every database call and log write.

A worker of `opus_import.steps.do_import_pool` computes an index's observations exactly
as the import's own process does, through the same code, but it has no database
connection and must not write to the import's log files. So wherever that code would ask
the database for something or write a message, it asks the context's `Capture` instead:

* a new row id is a `LocalId`, numbered from zero per table within the worker's task;
* a value of a mult column is a `MultRef` to the mult resolution the worker recorded
  for it, since only the import's process knows the id the value has or will get;
* a ``mult_list`` column holding either is a `DeferredJson`, the list before it is
  turned into JSON;
* a log message, a Python warning, and a ``pdsfile`` log call are each recorded with
  the index row and filespec the worker was on.

The import's process replays a task's events in order (`Capture.events`), turning each
placeholder into the value the serial loop would have computed at that point, so the
tables and the log come out the same whatever the number of workers.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class LocalId:
    """A row id a worker handed out, to be rebased by the import's process.

    Attributes:
        table: The table the id belongs to.
        number: The id's position among the ids of that table in the worker's task,
            from zero.
    """

    table: str
    number: int


@dataclass(frozen=True)
class MultRef:
    """A mult id a worker could not know, standing for one recorded resolution.

    Attributes:
        number: The resolution's position among the task's mult events, from zero.
    """

    number: int


@dataclass(frozen=True)
class DeferredJson:
    """A ``mult_list`` column's values, turned into JSON once their ids are known.

    Attributes:
        values: The list's entries, any of which may be a placeholder.
    """

    values: tuple[Any, ...]


#: The placeholder types, for an ``isinstance`` check.
DEFERRED_TYPES = (LocalId, MultRef, DeferredJson)


def is_deferred(value: Any) -> bool:
    """Return whether a value is a placeholder the import's process has to resolve.

    Parameters:
        value: A column value.

    Returns:
        True for a `LocalId`, `MultRef`, or `DeferredJson`.
    """
    return isinstance(value, DEFERRED_TYPES)


def json_list(values: list[Any]) -> str | DeferredJson:
    """Return a ``mult_list`` column's stored form.

    Parameters:
        values: The column's values, without the missing ones.

    Returns:
        The values as a JSON array, or a `DeferredJson` when any of them is a
        placeholder.
    """
    if any(is_deferred(value) for value in values):
        return DeferredJson(tuple(values))
    return json.dumps(values)


#: One recorded event -- its kind, the index row number and primary filespec the worker
#: was on, then what the kind needs.
Event = tuple[Any, ...]


@dataclass
class Capture:
    """The record a worker's context keeps of one task.

    Attributes:
        events: Every row, mult resolution, log message, Python warning, and
            ``pdsfile`` log call, in the order the serial loop would have produced them.
        id_counts: How many ids the task handed out per table.
        mult_count: How many mult resolutions the task recorded.
    """

    events: list[Event] = field(default_factory=list)
    id_counts: dict[str, int] = field(default_factory=dict)
    mult_count: int = 0

    def next_id(self, table: str) -> LocalId:
        """Hand out the task's next id for a table.

        Parameters:
            table: The table.

        Returns:
            The placeholder for the id.
        """
        number = self.id_counts.get(table, 0)
        self.id_counts[table] = number + 1
        return LocalId(table, number)

    def mult(
        self, position: tuple[Any, Any], table: str, field_name: str, values: tuple[Any, ...]
    ) -> MultRef:
        """Record a value of a mult column, to be resolved by the import's process.

        Parameters:
            position: The index row number and primary filespec the worker is on.
            table: The observation table the column belongs to.
            field_name: The column.
            values: `opus_import.steps.do_import_mult.update_mult_table`'s arguments
                after its column definition: the value, label, display flag, pin,
                grouping, and group pin.

        Returns:
            The placeholder for the id the value will have.
        """
        self.events.append(('mult', *position, table, field_name, values))
        reference = MultRef(self.mult_count)
        self.mult_count += 1
        return reference

    def row(self, position: tuple[Any, Any], table: str, row: dict[str, Any]) -> None:
        """Record a computed row.

        Parameters:
            position: The index row number and primary filespec the worker is on.
            table: The table the row goes into, or the surface geometry category it was
                computed under.
            row: The row, which may hold placeholders.
        """
        self.events.append(('row', *position, table, row))

    def log(self, position: tuple[Any, Any], method: str, args: tuple[Any, ...]) -> None:
        """Record a call of one of `opus_import.context.ImportLog`'s methods.

        Parameters:
            position: The index row number and primary filespec the worker is on.
            method: The method's name.
            args: Its arguments.
        """
        self.events.append(('log', *position, method, args))

    def warning(
        self,
        position: tuple[Any, Any],
        text: str,
        category: type[Warning],
        filename: str,
        lineno: int,
    ) -> None:
        """Record a Python warning the worker's filters let through.

        Parameters:
            position: The index row number and primary filespec the worker is on.
            text: The warning's text.
            category: Its class.
            filename: The file it is attributed to.
            lineno: The line it is attributed to.
        """
        self.events.append(('warning', *position, text, category, filename, lineno))

    def pdsfile_log(
        self,
        position: tuple[Any, Any],
        owner: str,
        method: str,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> None:
        """Record a call of a ``pdsfile`` class's logger.

        Parameters:
            position: The index row number and primary filespec the worker is on.
            owner: The class whose ``LOGGER`` was called, as module and qualified name.
            method: The logger method.
            args: Its positional arguments.
            kwargs: Its keyword arguments.
        """
        self.events.append(('pdsfile', *position, owner, method, args, kwargs))
