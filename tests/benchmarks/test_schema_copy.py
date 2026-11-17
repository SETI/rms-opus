"""How a schema is copied in the import's layout: keys built after the rows are in."""

from __future__ import annotations

from typing import Any

from benchmarks import schema_copy

#: A table as ``SHOW CREATE TABLE`` prints it, one element a line.
_DEFINITION = '\n'.join(
    [
        'CREATE TABLE `obs_child` (',
        '  `obs_general_id` int unsigned NOT NULL,',
        '  `opus_id` varchar(50) NOT NULL,',
        '  `value` smallint unsigned DEFAULT NULL,',
        '  `note` text,',
        '  PRIMARY KEY (`obs_general_id`),',
        '  UNIQUE KEY `opus_id` (`opus_id`),',
        '  KEY `value` (`value`,`obs_general_id`),',
        '  FULLTEXT KEY `note` (`note`) /*!50100 WITH PARSER `ngram` */ ,',
        '  CONSTRAINT `obs_child_ibfk_1` FOREIGN KEY (`obs_general_id`) REFERENCES '
        '`obs_general_rows` (`id`) ON DELETE CASCADE,',
        '  CONSTRAINT `small` CHECK ((`value` < 1000))',
        ') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 STATS_SAMPLE_PAGES=500',
    ]
)


def test_a_definition_keeps_its_columns_primary_key_and_checks_alone() -> None:
    """The secondary keys and foreign keys are set apart, each as printed."""
    layout = schema_copy.split_secondary_keys(_DEFINITION)
    assert layout.definition == '\n'.join(
        [
            'CREATE TABLE `obs_child` (',
            '  `obs_general_id` int unsigned NOT NULL,',
            '  `opus_id` varchar(50) NOT NULL,',
            '  `value` smallint unsigned DEFAULT NULL,',
            '  `note` text,',
            '  PRIMARY KEY (`obs_general_id`),',
            '  CONSTRAINT `small` CHECK ((`value` < 1000))',
            ') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 STATS_SAMPLE_PAGES=500',
        ]
    )
    assert layout.keys == (
        'UNIQUE KEY `opus_id` (`opus_id`)',
        'KEY `value` (`value`,`obs_general_id`)',
    )
    assert layout.separate_keys == ('FULLTEXT KEY `note` (`note`) /*!50100 WITH PARSER `ngram` */',)
    assert layout.foreign_keys == (
        'CONSTRAINT `obs_child_ibfk_1` FOREIGN KEY (`obs_general_id`) REFERENCES '
        '`obs_general_rows` (`id`) ON DELETE CASCADE',
    )


def test_the_element_left_last_loses_its_comma() -> None:
    """With the keys after the primary key gone, the primary key ends the list."""
    definition = 'CREATE TABLE `t` (\n  `id` int NOT NULL,\n  PRIMARY KEY (`id`),\n  KEY `k` (`id`)\n) ENGINE=InnoDB'
    layout = schema_copy.split_secondary_keys(definition)
    assert (
        layout.definition
        == 'CREATE TABLE `t` (\n  `id` int NOT NULL,\n  PRIMARY KEY (`id`)\n) ENGINE=InnoDB'
    )


def test_a_table_without_secondary_keys_is_left_as_it_is() -> None:
    """Nothing is set apart, and nothing loses a comma."""
    definition = 'CREATE TABLE `t` (\n  `id` int NOT NULL,\n  PRIMARY KEY (`id`)\n) ENGINE=InnoDB'
    layout = schema_copy.split_secondary_keys(definition)
    assert layout.definition == definition
    assert layout.key_statements('`d`.`t`') == []
    assert layout.foreign_key_statement('`d`.`t`') is None


def test_the_keys_are_added_together_and_each_fulltext_key_alone() -> None:
    """One ALTER for the plain and unique keys, one per FULLTEXT key, one for the foreign
    keys."""
    layout = schema_copy.split_secondary_keys(_DEFINITION)
    assert layout.key_statements('`d`.`obs_child`') == [
        'ALTER TABLE `d`.`obs_child` ADD UNIQUE KEY `opus_id` (`opus_id`), '
        'ADD KEY `value` (`value`,`obs_general_id`)',
        'ALTER TABLE `d`.`obs_child` ADD FULLTEXT KEY `note` (`note`) '
        '/*!50100 WITH PARSER `ngram` */',
    ]
    assert layout.foreign_key_statement('`d`.`obs_child`') == (
        'ALTER TABLE `d`.`obs_child` ADD CONSTRAINT `obs_child_ibfk_1` FOREIGN KEY '
        '(`obs_general_id`) REFERENCES `obs_general_rows` (`id`) ON DELETE CASCADE'
    )


class _Connection:
    """A connection recording each statement, answering by the first key it holds."""

    def __init__(self, log: list[str]) -> None:
        """Record into the shared log."""
        self.log = log
        self._rows: list[tuple[Any, ...]] = []

    def cursor(self) -> _Connection:
        """Act as its own cursor."""
        return self

    def execute(self, statement: str, parameters: Any = None) -> None:
        """Record a statement and choose its answer."""
        self.log.append(statement)
        answers: dict[str, list[tuple[Any, ...]]] = {
            "TABLE_TYPE = 'BASE TABLE'": [('obs_child',), ('obs_general_rows',)],
            'SHOW CREATE TABLE': [('t', _DEFINITION)],
            "INDEX_NAME = 'PRIMARY'": [('obs_general_id',)],
            'GENERATION_EXPRESSION': [('obs_general_id',), ('value',)],
        }
        self._rows = next((rows for key, rows in answers.items() if key in statement), [])

    def fetchall(self) -> list[tuple[Any, ...]]:
        """Return the answer to the last statement."""
        return self._rows

    def close(self) -> None:
        """Nothing to close."""


class _Server:
    """A server whose connections share one log."""

    def __init__(self) -> None:
        self.log: list[str] = []

    def connect(self) -> _Connection:
        """Return a recording connection."""
        return _Connection(self.log)


def _clone(*, defer_keys: bool) -> list[str]:
    """Clone a two-table schema one table at a time, and return every statement issued."""
    server = _Server()
    schema_copy.clone_schema(
        server,  # type: ignore[arg-type]
        'src',
        'dst',
        version=None,
        connections=1,
        defer_keys=defer_keys,
    )
    return server.log


def test_a_deferred_clone_fills_each_table_in_key_order_before_adding_its_keys() -> None:
    """Created without secondary keys, filled ordered by the primary key, every key added
    after every fill, every foreign key after every key, in the copy's own schema."""
    log = _clone(defer_keys=True)
    creates = [text for text in log if text.startswith('CREATE TABLE')]
    assert all('KEY `value`' not in text and 'FOREIGN KEY' not in text for text in creates)
    inserts = [i for i, text in enumerate(log) if text.startswith('INSERT INTO')]
    assert all(log[i].endswith(' ORDER BY `obs_general_id`') for i in inserts)
    keys = [i for i, text in enumerate(log) if text.startswith('ALTER TABLE') and 'ADD KEY' in text]
    foreign = [i for i, text in enumerate(log) if 'ADD CONSTRAINT' in text]
    assert len(keys) == 2
    assert max(inserts) < min(keys)
    assert len(foreign) == 2
    assert max(keys) < min(foreign)
    assert log[min(foreign) - 1] == 'USE `dst`'


def test_a_plain_clone_keeps_every_key_in_its_create() -> None:
    """Without defer_keys a table is created whole and filled in no stated order."""
    log = _clone(defer_keys=False)
    assert [text for text in log if text.startswith('CREATE TABLE')] == [_DEFINITION] * 2
    assert not any(text.startswith('ALTER TABLE') for text in log)
    assert not any('ORDER BY `obs_general_id`' in text for text in log)
