"""Tests for the SQL assembly helpers in opus_app.apps.tools.sql_builder.

These need no database: they check what the builder renders, not what the server
does with it. The 100% branch-coverage gate measures `src/opus_app/apps/*`, so every
branch of the builder has to be exercised by the suite that gate reads --
which is why the integration coverage invocation runs `tests/opus_app` alongside
`integration_tests` in a single pass. Living here rather than in `integration_tests/`
is what also puts them in the holdings-free run on the GitHub-hosted CI.

What is worth pinning here, and why:

* **Identifier validation.** `quote_identifier` is the only thing standing
  between a runtime-computed name and the SQL text, because backticks quote an
  identifier without escaping a backtick inside one.
* **Parameter order.** The whole point of assembling a statement from parts is
  that the parameters come out in placeholder order no matter which order the
  caller added the parts in; a builder that got this wrong would silently swap
  two values of the same type.
* **The exact rendering of the search query.** `construct_query_string`'s output
  is asserted verbatim by test_search.py, so these cases pin the shapes that make
  that possible from the builder's side.
"""

import json
from pathlib import Path
from unittest import TestCase

import pytest

import opus_import
from opus_app.apps.tools import db_utils, sql_builder
from opus_support import UNSTORED_ASCII_CHARACTER


class SQLBuilderIdentifierTests(TestCase):
    """Quoting an identifier, and refusing one that cannot be quoted safely."""

    def test__quote_identifier_ok(self) -> None:
        "[test_sql_builder.py] quote_identifier: ordinary names"
        self.assertEqual(sql_builder.quote_identifier('obs_general'), '`obs_general`')
        self.assertEqual(sql_builder.quote_identifier('cache_1234'), '`cache_1234`')

    def test__quote_identifier_rejects_backtick(self) -> None:
        "[test_sql_builder.py] quote_identifier: a backtick cannot end the quoting"
        with self.assertRaises(sql_builder.SQLIdentifierError):
            sql_builder.quote_identifier('obs`general')

    def test__quote_identifier_rejects_qualified_name(self) -> None:
        "[test_sql_builder.py] quote_identifier: a dotted name is two identifiers"
        with self.assertRaises(sql_builder.SQLIdentifierError):
            sql_builder.quote_identifier('obs_general.id')

    def test__quote_identifier_rejects_empty(self) -> None:
        "[test_sql_builder.py] quote_identifier: the empty name"
        with self.assertRaises(sql_builder.SQLIdentifierError):
            sql_builder.quote_identifier('')

    def test__quote_identifier_rejects_non_string(self) -> None:
        "[test_sql_builder.py] quote_identifier: a non-string name"
        with self.assertRaises(sql_builder.SQLIdentifierError):
            sql_builder.quote_identifier(17)  # type: ignore[arg-type]  # a non-string name

    def test__column_qualified_and_bare(self) -> None:
        "[test_sql_builder.py] column: with and without a table"
        self.assertEqual(sql_builder.column('id', 'obs_general').sql, '`obs_general`.`id`')
        self.assertEqual(sql_builder.column('sort').sql, '`sort`')


class SQLBuilderExpressionTests(TestCase):
    """Building one expression: its SQL text and the parameters that go with it."""

    def test__value_is_a_placeholder(self) -> None:
        "[test_sql_builder.py] value: never renders the value into the SQL"
        expr = sql_builder.value("'; DROP TABLE obs_general; --")
        self.assertEqual(expr.sql, '%s')
        self.assertEqual(expr.params, ["'; DROP TABLE obs_general; --"])

    def test__binary_op_rejects_unknown_operator(self) -> None:
        "[test_sql_builder.py] binary_op: an operator outside the allowed set"
        with self.assertRaises(ValueError):
            sql_builder.binary_op(sql_builder.column('a', 't'), 'UNION', sql_builder.value(1))

    def test__binary_op_orders_params_left_to_right(self) -> None:
        "[test_sql_builder.py] binary_op: parameters follow their placeholders"
        expr = sql_builder.binary_op(sql_builder.value(1), '+', sql_builder.value(2))
        self.assertEqual(expr.sql, '%s + %s')
        self.assertEqual(expr.params, [1, 2])

    def test__columns_equal_has_no_spaces_and_no_params(self) -> None:
        "[test_sql_builder.py] columns_equal: the join-condition spelling"
        expr = sql_builder.columns_equal(
            sql_builder.column('id', 'obs_general'), sql_builder.column('obs_general_id', 'obs_pds')
        )
        self.assertEqual(expr.sql, '`obs_general`.`id`=`obs_pds`.`obs_general_id`')
        self.assertEqual(expr.params, [])

    def test__aliased_table_renders_the_keys_it_ignores_for_grouping(self) -> None:
        "[test_sql_builder.py] AliasedTable: IGNORE INDEX FOR GROUP BY after the alias"
        source = sql_builder.AliasedTable(
            'obs_surface_geometry_target', 's', ignore_for_group_by=('PRIMARY',)
        )
        self.assertEqual(
            source.render(),
            ('`obs_surface_geometry_target` AS `s` IGNORE INDEX FOR GROUP BY (`PRIMARY`)', []),
        )
        plain = sql_builder.AliasedTable('obs_surface_geometry_target', 's')
        self.assertEqual(plain.render(), ('`obs_surface_geometry_target` AS `s`', []))

    def test__exists_renders_its_source_and_condition_with_their_params(self) -> None:
        "[test_sql_builder.py] exists: an aliased source, a condition naming the outer table"
        expr = sql_builder.exists(
            sql_builder.AliasedTable('obs_surface_geometry_target', 's'),
            sql_builder.join_exprs(
                [
                    sql_builder.columns_equal(
                        sql_builder.column('obs_general_id', 's'),
                        sql_builder.column('id', 'obs_general'),
                    ),
                    sql_builder.in_values(sql_builder.column('target_name', 's'), [3, 7]),
                ],
                'AND',
            ),
        )
        self.assertEqual(
            expr.sql,
            'EXISTS (SELECT 1 FROM `obs_surface_geometry_target` AS `s` WHERE '
            '`s`.`obs_general_id`=`obs_general`.`id` AND `s`.`target_name` IN (%s,%s))',
        )
        self.assertEqual(expr.params, [3, 7])

    def test__columns_equal_rejects_a_parameter(self) -> None:
        "[test_sql_builder.py] columns_equal: a join condition never carries data"
        with self.assertRaises(ValueError):
            sql_builder.columns_equal(sql_builder.column('id', 'obs_general'), sql_builder.value(1))

    def test__is_null(self) -> None:
        "[test_sql_builder.py] is_null"
        self.assertEqual(sql_builder.is_null(sql_builder.column('t1', 'o')).sql, '`o`.`t1` IS NULL')

    def test__in_values(self) -> None:
        "[test_sql_builder.py] in_values: one placeholder per value"
        expr = sql_builder.in_values(sql_builder.column('planet_id', 'obs_general'), [3, 5])
        self.assertEqual(expr.sql, '`obs_general`.`planet_id` IN (%s,%s)')
        self.assertEqual(expr.params, [3, 5])

    def test__in_sequence(self) -> None:
        "[test_sql_builder.py] in_sequence: the sequence stays one parameter"
        expr = sql_builder.in_sequence(sql_builder.column('opus_id', 'obs_files'), ['a', 'b'])
        self.assertEqual(expr.sql, '`obs_files`.`opus_id` IN %s')
        self.assertEqual(expr.params, [['a', 'b']])

    def test__json_contains(self) -> None:
        "[test_sql_builder.py] json_contains: the MULTIGROUP membership test"
        expr = sql_builder.json_contains(sql_builder.column('target_name', 'obs_general'), '1')
        self.assertEqual(expr.sql, 'JSON_CONTAINS(`obs_general`.`target_name`,%s)')
        self.assertEqual(expr.params, ['1'])

    def test__json_extract_first(self) -> None:
        "[test_sql_builder.py] json_extract_first: the MULTIGROUP join key"
        expr = sql_builder.json_extract_first(sql_builder.column('target_name', 'obs_general'))
        self.assertEqual(expr.sql, 'JSON_EXTRACT(`obs_general`.`target_name`, "$[0]")')

    def test__angular_separation(self) -> None:
        "[test_sql_builder.py] angular_separation: the longitude distance"
        expr = sql_builder.angular_separation(
            sql_builder.column('j2000_longitude', 'obs_ring_geometry'), 30.0
        )
        self.assertEqual(
            expr.sql, 'ABS(MOD(%s - `obs_ring_geometry`.`j2000_longitude` + 540., 360.) - 180.)'
        )
        self.assertEqual(expr.params, [30.0])

    def test__aggregates(self) -> None:
        "[test_sql_builder.py] COUNT/SUM/MIN/MAX"
        col = sql_builder.column('size', 'obs_files')
        self.assertEqual(sql_builder.count_star().sql, 'COUNT(*)')
        self.assertEqual(sql_builder.count_distinct(col).sql, 'COUNT(DISTINCT `obs_files`.`size`)')
        self.assertEqual(sql_builder.sum_of(col).sql, 'SUM(`obs_files`.`size`)')
        self.assertEqual(sql_builder.min_of(col).sql, 'MIN(`obs_files`.`size`)')
        self.assertEqual(sql_builder.max_of(col).sql, 'MAX(`obs_files`.`size`)')

    def test__join_exprs_is_flat(self) -> None:
        "[test_sql_builder.py] join_exprs: no parentheses are added"
        expr = sql_builder.join_exprs(
            [
                sql_builder.binary_op(sql_builder.column('a', 't'), '>=', sql_builder.value(1)),
                sql_builder.binary_op(sql_builder.column('b', 't'), '<=', sql_builder.value(2)),
            ],
            'AND',
        )
        self.assertEqual(expr.sql, '`t`.`a` >= %s AND `t`.`b` <= %s')
        self.assertEqual(expr.params, [1, 2])

    def test__join_exprs_rejects_unknown_operator(self) -> None:
        "[test_sql_builder.py] join_exprs: only AND and OR"
        with self.assertRaises(ValueError):
            sql_builder.join_exprs([sql_builder.value(1)], 'XOR')

    def test__combine_exprs_single_is_unparenthesized(self) -> None:
        "[test_sql_builder.py] combine_exprs: one clause is left alone"
        one = sql_builder.binary_op(sql_builder.column('a', 't'), '=', sql_builder.value(1))
        self.assertEqual(sql_builder.combine_exprs([one], 'OR').sql, '`t`.`a` = %s')

    def test__combine_exprs_multiple_are_parenthesized(self) -> None:
        "[test_sql_builder.py] combine_exprs: more than one clause gets parentheses"
        one = sql_builder.binary_op(sql_builder.column('a', 't'), '=', sql_builder.value(1))
        two = sql_builder.binary_op(sql_builder.column('b', 't'), '=', sql_builder.value(2))
        expr = sql_builder.combine_exprs([one, two], 'OR')
        self.assertEqual(expr.sql, '(`t`.`a` = %s) OR (`t`.`b` = %s)')
        self.assertEqual(expr.params, [1, 2])

    def test__combine_exprs_empty(self) -> None:
        "[test_sql_builder.py] combine_exprs: no clauses at all"
        expr = sql_builder.combine_exprs([], 'OR')
        self.assertEqual(expr.sql, '')
        self.assertEqual(expr.params, [])

    def test__parenthesize(self) -> None:
        "[test_sql_builder.py] parenthesize"
        expr = sql_builder.parenthesize(sql_builder.value(1))
        self.assertEqual(expr.sql, '(%s)')
        self.assertEqual(expr.params, [1])


class SQLBuilderSelectTests(TestCase):
    """Assembling a SELECT, and the order its parameters come out in."""

    def test__select_matches_the_search_query_shape(self) -> None:
        "[test_sql_builder.py] Select: the exact text construct_query_string emits"
        select = sql_builder.Select()
        select.add_column(sql_builder.column('id', 'obs_general'))
        from_source = select.add_from('obs_general')
        from_source.add_join(
            'LEFT',
            'obs_pds',
            sql_builder.columns_equal(
                sql_builder.column('id', 'obs_general'),
                sql_builder.column('obs_general_id', 'obs_pds'),
            ),
        )
        select.add_where(
            sql_builder.binary_op(
                sql_builder.column('primary_filespec', 'obs_pds'),
                'LIKE',
                sql_builder.value('%C11399XX%'),
            )
        )
        select.add_order_by(sql_builder.column('time1', 'obs_general'), descending=False)
        sql, params = select.build()
        self.assertEqual(
            sql,
            'SELECT `obs_general`.`id` FROM `obs_general`'
            ' LEFT JOIN `obs_pds` ON'
            ' `obs_general`.`id`=`obs_pds`.`obs_general_id`'
            ' WHERE `obs_pds`.`primary_filespec` LIKE %s'
            ' ORDER BY `obs_general`.`time1` ASC',
        )
        self.assertEqual(params, ['%C11399XX%'])

    def test__select_params_follow_placeholder_order_not_call_order(self) -> None:
        "[test_sql_builder.py] Select: parameters come out in placeholder order"
        select = sql_builder.Select()
        # Deliberately added back to front: WHERE first, then the join, then the
        # result column, which is the reverse of where they appear in the text.
        select.add_where(
            sql_builder.binary_op(sql_builder.column('c', 'a'), '=', sql_builder.value('where'))
        )
        from_source = select.add_from('a')
        from_source.add_join(
            'INNER',
            'b',
            sql_builder.binary_op(sql_builder.column('c', 'b'), '=', sql_builder.value('join')),
        )
        select.add_column(sql_builder.value('column'))
        sql, params = select.build()
        self.assertEqual(
            sql, 'SELECT %s FROM `a` INNER JOIN `b` ON `b`.`c` = %s WHERE `a`.`c` = %s'
        )
        self.assertEqual(params, ['column', 'join', 'where'])

    def test__select_distinct_hint_group_limit_offset(self) -> None:
        "[test_sql_builder.py] Select: DISTINCT, the optimizer hint, GROUP BY, LIMIT/OFFSET"
        select = sql_builder.Select(distinct=True, max_execution_time=5000)
        select.add_column(sql_builder.column('short_name', 'obs_files'), alias='short')
        select.add_column(sql_builder.count_star(), alias='n')
        select.add_from('obs_files')
        select.add_group_by(sql_builder.column('short'))
        select.add_order_by(sql_builder.column('short'), descending=True)
        select.limit(11)
        select.offset(20)
        sql, params = select.build()
        self.assertEqual(
            sql,
            'SELECT /*+ MAX_EXECUTION_TIME(5000) */ DISTINCT'
            ' `obs_files`.`short_name` AS `short`,COUNT(*) AS `n`'
            ' FROM `obs_files` GROUP BY `short` ORDER BY `short` DESC'
            ' LIMIT 11 OFFSET 20',
        )
        self.assertEqual(params, [])

    def test__select_rejects_non_int_limit_and_offset(self) -> None:
        "[test_sql_builder.py] Select: LIMIT/OFFSET are rendered literally, so they must be ints"
        select = sql_builder.Select()
        with self.assertRaises(ValueError):
            select.limit('10; DROP TABLE obs_general')  # type: ignore[arg-type]  # not an int
        with self.assertRaises(ValueError):
            select.offset('0; DROP TABLE obs_general')  # type: ignore[arg-type]  # not an int

    def test__select_rejects_non_int_max_execution_time(self) -> None:
        "[test_sql_builder.py] Select: the optimizer hint is rendered literally too"
        with self.assertRaises(ValueError):
            sql_builder.Select(max_execution_time='1) */ UNION SELECT 1 /*')  # type: ignore[arg-type]  # not an int

    def test__select_rejects_unknown_join_kind(self) -> None:
        "[test_sql_builder.py] Select: only INNER and LEFT joins"
        select = sql_builder.Select()
        select.add_column(sql_builder.column('id', 'a'))
        select.add_from('a').add_join('RIGHT', 'b', None)
        with self.assertRaises(ValueError):
            select.build()

    def test__select_comma_sources_and_subquery(self) -> None:
        "[test_sql_builder.py] Select: a derived table and a second comma source"
        inner = sql_builder.Select(distinct=True)
        inner.add_column(sql_builder.column('short_name', 'obs_files'))
        inner.add_from('obs_files')
        inner.add_where(
            sql_builder.binary_op(
                sql_builder.column('session_id', 'cart'), '=', sql_builder.value('sess')
            )
        )

        outer = sql_builder.Select()
        outer.add_column(sql_builder.column('short_name', 't1'))
        outer.add_from(sql_builder.Subquery(inner, 't1'))
        outer.add_from('obs_files')
        outer.add_where(
            sql_builder.columns_equal(
                sql_builder.column('short_name', 'obs_files'),
                sql_builder.column('short_name', 't1'),
            )
        )
        sql, params = outer.build()
        self.assertEqual(
            sql,
            'SELECT `t1`.`short_name` FROM (SELECT DISTINCT'
            ' `obs_files`.`short_name` FROM `obs_files`'
            ' WHERE `cart`.`session_id` = %s) AS `t1`,`obs_files`'
            ' WHERE `obs_files`.`short_name`=`t1`.`short_name`',
        )
        self.assertEqual(params, ['sess'])

    def test__select_json_table_source(self) -> None:
        "[test_sql_builder.py] Select: the JSON_TABLE join the mult counts use"
        select = sql_builder.Select()
        select.add_column(sql_builder.column('_mult_val_', 'obs_general'))
        select.add_from('obs_general').add_join(
            'INNER',
            sql_builder.JSONTable(
                source_column=sql_builder.column('target_name', 'obs_general'),
                value_column='_mult_val_',
                alias='obs_general',
            ),
        )
        sql, _params = select.build()
        self.assertEqual(
            sql,
            'SELECT `obs_general`.`_mult_val_` FROM `obs_general`'
            ' INNER JOIN JSON_TABLE(`obs_general`.`target_name`, "$[*]"'
            ' COLUMNS (`_mult_val_` TEXT PATH "$")) `obs_general`',
        )


class SQLBuilderStatementTests(TestCase):
    """The statements built around a SELECT: INSERT ... SELECT, DELETE and the rest."""

    def test__search_results_source(self) -> None:
        "[test_sql_builder.py] search_results_source: one search's rows, shaped id and sort_order"
        select = sql_builder.Select()
        select.add_column(sql_builder.column('sort_order', sql_builder.SEARCH_RESULTS_ALIAS))
        select.add_from('obs_general').add_join(
            'INNER',
            sql_builder.search_results_source(12),
            sql_builder.columns_equal(
                sql_builder.column('id', sql_builder.SEARCH_RESULTS_ALIAS),
                sql_builder.column('id', 'obs_general'),
            ),
        )
        sql, params = select.build()
        self.assertEqual(
            sql,
            'SELECT `results`.`sort_order` FROM `obs_general` INNER JOIN'
            ' (SELECT `search_results`.`obs_general_id` AS `id`,`search_results`.`sort_order`'
            ' FROM `search_results` WHERE `search_results`.`search_id` = %s) AS `results`'
            ' ON `results`.`id`=`obs_general`.`id`',
        )
        self.assertEqual(params, [12])

    def test__between(self) -> None:
        "[test_sql_builder.py] between: both bounds are parameters, after the expression's"
        self.assertEqual(
            sql_builder.between(sql_builder.column('sort_order', 'results'), 3, 7),
            sql_builder.Expr('`results`.`sort_order` BETWEEN %s AND %s', [3, 7]),
        )

    def test__sort_order_range(self) -> None:
        "[test_sql_builder.py] sort_order_range: the window after an offset, numbered from 1"
        self.assertEqual(
            sql_builder.sort_order_range('results', 200, 100),
            sql_builder.Expr('`results`.`sort_order` BETWEEN %s AND %s', [201, 300]),
        )

    def test__row_number(self) -> None:
        "[test_sql_builder.py] row_number: the window's ORDER BY renders as Select's does"
        self.assertEqual(
            sql_builder.row_number(
                [
                    (sql_builder.column('time1', 'obs_general'), True),
                    (sql_builder.column('opus_id', 'obs_general'), None),
                    (
                        sql_builder.binary_op(sql_builder.column('x'), '+', sql_builder.value(1)),
                        False,
                    ),
                ]
            ),
            sql_builder.Expr(
                'ROW_NUMBER() OVER (ORDER BY `obs_general`.`time1` DESC,`obs_general`.`opus_id`,'
                '`x` + %s ASC)',
                [1],
            ),
        )

    def test__row_number_without_an_order(self) -> None:
        "[test_sql_builder.py] row_number: no order terms number the rows in no stated order"
        self.assertEqual(sql_builder.row_number([]), sql_builder.Expr('ROW_NUMBER() OVER ()', []))

    def test__delete_from(self) -> None:
        "[test_sql_builder.py] delete_from"
        sql, params = sql_builder.delete_from(
            'cart',
            sql_builder.binary_op(
                sql_builder.column('session_id', 'cart'), '=', sql_builder.value('sess')
            ),
        )
        self.assertEqual(sql, 'DELETE FROM `cart` WHERE `cart`.`session_id` = %s')
        self.assertEqual(params, ['sess'])

    def test__delete_joined(self) -> None:
        "[test_sql_builder.py] delete_joined: the rows come from a join"
        from_source = sql_builder.FromSource('cart')
        from_source.add_join(
            'INNER',
            'cache_12',
            sql_builder.columns_equal(
                sql_builder.column('id', 'cache_12'), sql_builder.column('obs_general_id', 'cart')
            ),
        )
        sql, params = sql_builder.delete_joined(
            'cart',
            from_source,
            sql_builder.binary_op(
                sql_builder.column('sort_order', 'cache_12'), '>=', sql_builder.value(4)
            ),
        )
        self.assertEqual(
            sql,
            'DELETE `cart` FROM `cart` INNER JOIN `cache_12`'
            ' ON `cache_12`.`id`=`cart`.`obs_general_id`'
            ' WHERE `cache_12`.`sort_order` >= %s',
        )
        self.assertEqual(params, [4])

    def test__replace_into_values(self) -> None:
        "[test_sql_builder.py] replace_into_values: one placeholder per column"
        self.assertEqual(
            sql_builder.replace_into_values('cart', ('session_id', 'opus_id')),
            'REPLACE INTO `cart` (`session_id`,`opus_id`) VALUES (%s,%s)',
        )

    def test__insert_into_select(self) -> None:
        "[test_sql_builder.py] insert_into_select: a search build's statement"
        select = sql_builder.Select()
        select.add_column(sql_builder.value(12))
        select.add_column(
            sql_builder.row_number([(sql_builder.column('opus_id', 'obs_general'), False)])
        )
        select.add_column(sql_builder.column('id', 'obs_general'))
        select.add_from('obs_general')
        sql, params = sql_builder.insert_into_select(
            'search_results', ('search_id', 'sort_order', 'obs_general_id'), select
        )
        self.assertEqual(
            sql,
            'INSERT INTO `search_results` (`search_id`,`sort_order`,`obs_general_id`)'
            ' SELECT %s,ROW_NUMBER() OVER (ORDER BY `obs_general`.`opus_id` ASC),'
            '`obs_general`.`id` FROM `obs_general`',
        )
        self.assertEqual(params, [12])

    def test__replace_into_select(self) -> None:
        "[test_sql_builder.py] replace_into_select"
        select = sql_builder.Select()
        select.add_column(sql_builder.value('sess'))
        select.add_column(sql_builder.column('opus_id', 'obs_general'))
        select.add_from('obs_general')
        sql, params = sql_builder.replace_into_select('cart', ('session_id', 'opus_id'), select)
        self.assertEqual(
            sql,
            'REPLACE INTO `cart` (`session_id`,`opus_id`)'
            ' SELECT %s,`obs_general`.`opus_id` FROM `obs_general`',
        )
        self.assertEqual(params, ['sess'])

    def test__update(self) -> None:
        "[test_sql_builder.py] update: the SET values are parameters too"
        sql, params = sql_builder.update(
            'cart',
            [('recycled', 0)],
            sql_builder.binary_op(
                sql_builder.column('session_id', 'cart'), '=', sql_builder.value('sess')
            ),
        )
        self.assertEqual(sql, 'UPDATE `cart` SET `recycled`=%s WHERE `cart`.`session_id` = %s')
        self.assertEqual(params, [0, 'sess'])


class SQLBuilderASCIITests(TestCase):
    """Text bound for a comparison with an ASCII column, and which columns are ASCII."""

    def test__ascii_comparable_keeps_ascii(self) -> None:
        "[test_sql_builder.py] ascii_comparable: ASCII text, case and punctuation kept"
        self.assertEqual(
            sql_builder.ascii_comparable('CO-ISS-n1460960653_%\\'), 'CO-ISS-n1460960653_%\\'
        )

    def test__ascii_comparable_folds_accents_as_the_old_collation_did(self) -> None:
        "[test_sql_builder.py] ascii_comparable: decomposed, the combining marks dropped"
        self.assertEqual(sql_builder.ascii_comparable('Müller'), 'Muller')
        self.assertEqual(sql_builder.ascii_comparable('Európa'), 'Europa')
        self.assertEqual(sql_builder.ascii_comparable('cö-iss-ñ'), 'co-iss-n')
        # A compatibility form decomposes to its ASCII letters.
        self.assertEqual(sql_builder.ascii_comparable('ﬁle'), 'file')

    def test__ascii_comparable_replaces_what_has_no_ascii_form(self) -> None:
        "[test_sql_builder.py] ascii_comparable: one unstored character for each such one"
        unstored = UNSTORED_ASCII_CHARACTER
        # A sharp s, a degree sign and an emoji have no decomposition into ASCII.
        self.assertEqual(
            sql_builder.ascii_comparable('straße°🪐'), f'stra{unstored}e{unstored * 2}'
        )
        self.assertTrue(unstored.isascii())

    def test__ascii_comparable_for_a_regex_maps_no_compatibility_character(self) -> None:
        "[test_sql_builder.py] ascii_comparable: canonical decomposition alone for a regex"
        unstored = UNSTORED_ASCII_CHARACTER
        # The accents go; a full-width full stop and asterisk stay characters, not operators.
        self.assertEqual(
            sql_builder.ascii_comparable('VGÍSS\uff0e62\uff0a', compatibility=False),
            f'VGISS{unstored}62{unstored}',
        )
        self.assertEqual(sql_builder.ascii_comparable('VGÍSS\uff0e62\uff0a'), 'VGISS.62*')

    def test__ascii_collation_key_equals_what_the_collation_does(self) -> None:
        "[test_sql_builder.py] ascii_collation_key: folded, unpadded, without case"
        self.assertEqual(
            sql_builder.ascii_collation_key('CÓ-ISS-N1460960653  '), 'co-iss-n1460960653'
        )
        self.assertEqual(
            sql_builder.ascii_collation_key('co-iss-n1460960653'), 'co-iss-n1460960653'
        )
        # A leading space and a trailing tab are kept, as the collation keeps them.
        self.assertEqual(sql_builder.ascii_collation_key(' a\t'), ' a\t')

    def test__generated_models_declare_the_ascii_columns(self) -> None:
        "[test_sql_builder.py] is_ascii_column: as each schema's field_charset says"
        ascii_columns, other_strings = _schema_string_columns()
        self.assertIn(('obs_general', 'opus_id'), ascii_columns)
        self.assertEqual(
            other_strings, {('obs_pds', 'note'), ('obs_mission_hubble', 'hst_pi_name')}
        )
        for table, column in sorted(ascii_columns):
            with self.subTest(table=table, column=column):
                self.assertTrue(db_utils.is_ascii_column(table, column))
        for table, column in sorted(other_strings | {('obs_files', 'short_name')}):
            with self.subTest(table=table, column=column):
                self.assertFalse(db_utils.is_ascii_column(table, column))


def _schema_string_columns() -> tuple[set[tuple[str, str]], set[tuple[str, str]]]:
    """Return the ASCII columns of the tables with a model, and the other STRING columns.

    Returns:
        Every column a packaged schema gives ``field_charset``, in a table the ``search``
        app has a model for; and every column whose ``pi_form_type`` is ``STRING`` and
        that has none.
    """
    ascii_columns: set[tuple[str, str]] = set()
    other_strings: set[tuple[str, str]] = set()
    for path in sorted((Path(opus_import.__file__).parent / 'table_schemas').glob('*.json')):
        entries = json.loads(path.read_text(encoding='utf-8'))
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if 'field_name' not in entry:
                continue
            key = (path.stem, entry['field_name'])
            if entry.get('field_charset') == 'ascii':
                try:
                    db_utils.table_model_from_name(path.stem)
                except LookupError:
                    continue
                ascii_columns.add(key)
            elif entry.get('pi_form_type') == 'STRING':
                other_strings.add(key)
    return ascii_columns, other_strings


@pytest.mark.parametrize(
    ('text', 'phrase'),
    [
        ('CO', '"CO"'),
        ('COISS_', '"COISS_"'),
        ('co-iss-n154673', '"n154673"'),
        ('ab"cd', '"ab"'),
        ('x*yz+12 3', '"yz"'),
        ('100% done', '"done"'),
    ],
    ids=['two-letters', 'underscore', 'longest-word', 'quote', 'operators', 'wildcard'],
)
def test_fulltext_match_searches_the_longest_word_as_a_phrase(text: str, phrase: str) -> None:
    """The phrase holds only letters, digits and underscores, so no character the ngram
    parser breaks a token at and no boolean operator reaches the server."""
    expr = sql_builder.fulltext_match(sql_builder.column('bundle_id', 'obs_pds'), text)
    assert expr == sql_builder.Expr(
        'MATCH(`obs_pds`.`bundle_id`) AGAINST (%s IN BOOLEAN MODE)', [phrase]
    )


@pytest.mark.parametrize('text', ['', 'a', 'a-b', '-', 'é'], ids=repr)
def test_fulltext_match_is_none_for_text_without_a_two_character_word(text: str) -> None:
    """The index holds no token shorter than the ngram token size."""
    assert sql_builder.fulltext_match(sql_builder.column('bundle_id', 'obs_pds'), text) is None


def test_fulltext_match_keeps_the_columns_parameters_first() -> None:
    """A column expression's own parameters come before the phrase."""
    expr = sql_builder.fulltext_match(sql_builder.Expr('f(%s)', [7]), 'abc')
    assert expr is not None
    assert expr.params == [7, '"abc"']


@pytest.mark.parametrize(
    ('args', 'abandoned'),
    [
        ((db_utils.MYSQL_EXECUTION_TIME_EXCEEDED, 'Query execution was interrupted'), True),
        (
            (
                db_utils.MYSQL_STORAGE_ENGINE_ERROR,
                "Got error 188 - 'FTS query exceeds result cache limit' from storage engine",
            ),
            True,
        ),
        ((db_utils.MYSQL_STORAGE_ENGINE_ERROR, 'Got error 1880 from storage engine'), False),
        ((db_utils.MYSQL_STORAGE_ENGINE_ERROR,), False),
        ((db_utils.MYSQL_LOCK_WAIT_TIMEOUT, 'Lock wait timeout exceeded'), False),
        ((), False),
    ],
    ids=['time-limit', 'result-cache', 'other-engine-error', 'no-message', 'lock-wait', 'bare'],
)
def test_an_abandoned_query_is_a_time_limit_or_the_full_text_result_cache(
    args: tuple[object, ...], abandoned: bool
) -> None:
    """The two errors after which another statement may answer the string choices."""
    assert db_utils.is_abandoned_query_error(Exception(*args)) is abandoned
