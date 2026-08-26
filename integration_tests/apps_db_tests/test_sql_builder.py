# integration_tests/apps_db_tests/test_sql_builder.py

"""Tests for the SQL assembly helpers in opus_app.apps.tools.sql_builder.

These need no database: they check what the builder renders, not what the server
does with it. They live in this suite rather than in `tests/` because the 100%
branch-coverage gate measures `src/opus_app/apps/*`, and every branch of the
builder has to be exercised by the suite that gate reads. PR-18 creates the
holdings-free Django suite these could later move to.

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

from unittest import TestCase

from opus_app.apps.tools import sql_builder


class SQLBuilderIdentifierTests(TestCase):
    """Quoting an identifier, and refusing one that cannot be quoted safely."""

    def test__quote_identifier_ok(self) -> None:
        "[test_sql_builder.py] quote_identifier: ordinary names"
        self.assertEqual(sql_builder.quote_identifier('obs_general'),
                         '`obs_general`')
        self.assertEqual(sql_builder.quote_identifier('cache_1234'),
                         '`cache_1234`')

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
            sql_builder.quote_identifier(17)  # type: ignore[arg-type]

    def test__column_qualified_and_bare(self) -> None:
        "[test_sql_builder.py] column: with and without a table"
        self.assertEqual(sql_builder.column('id', 'obs_general').sql,
                         '`obs_general`.`id`')
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
            sql_builder.binary_op(sql_builder.column('a', 't'), 'UNION',
                                  sql_builder.value(1))

    def test__binary_op_orders_params_left_to_right(self) -> None:
        "[test_sql_builder.py] binary_op: parameters follow their placeholders"
        expr = sql_builder.binary_op(sql_builder.value(1), '+',
                                     sql_builder.value(2))
        self.assertEqual(expr.sql, '%s + %s')
        self.assertEqual(expr.params, [1, 2])

    def test__columns_equal_has_no_spaces_and_no_params(self) -> None:
        "[test_sql_builder.py] columns_equal: the join-condition spelling"
        expr = sql_builder.columns_equal(sql_builder.column('id', 'obs_general'),
                                         sql_builder.column('obs_general_id',
                                                            'obs_pds'))
        self.assertEqual(expr.sql,
                         '`obs_general`.`id`=`obs_pds`.`obs_general_id`')
        self.assertEqual(expr.params, [])

    def test__columns_equal_rejects_a_parameter(self) -> None:
        "[test_sql_builder.py] columns_equal: a join condition never carries data"
        with self.assertRaises(ValueError):
            sql_builder.columns_equal(sql_builder.column('id', 'obs_general'),
                                      sql_builder.value(1))

    def test__is_null(self) -> None:
        "[test_sql_builder.py] is_null"
        self.assertEqual(sql_builder.is_null(sql_builder.column('t1', 'o')).sql,
                         '`o`.`t1` IS NULL')

    def test__in_values(self) -> None:
        "[test_sql_builder.py] in_values: one placeholder per value"
        expr = sql_builder.in_values(sql_builder.column('planet_id',
                                                        'obs_general'),
                                     [3, 5])
        self.assertEqual(expr.sql, '`obs_general`.`planet_id` IN (%s,%s)')
        self.assertEqual(expr.params, [3, 5])

    def test__in_sequence(self) -> None:
        "[test_sql_builder.py] in_sequence: the sequence stays one parameter"
        expr = sql_builder.in_sequence(sql_builder.column('opus_id',
                                                          'obs_files'),
                                       ['a', 'b'])
        self.assertEqual(expr.sql, '`obs_files`.`opus_id` IN %s')
        self.assertEqual(expr.params, [['a', 'b']])

    def test__json_contains(self) -> None:
        "[test_sql_builder.py] json_contains: the MULTIGROUP membership test"
        expr = sql_builder.json_contains(
            sql_builder.column('target_name', 'obs_general'), '1')
        self.assertEqual(expr.sql,
                         'JSON_CONTAINS(`obs_general`.`target_name`,%s)')
        self.assertEqual(expr.params, ['1'])

    def test__json_extract_first(self) -> None:
        "[test_sql_builder.py] json_extract_first: the MULTIGROUP join key"
        expr = sql_builder.json_extract_first(
            sql_builder.column('target_name', 'obs_general'))
        self.assertEqual(expr.sql,
                         'JSON_EXTRACT(`obs_general`.`target_name`, "$[0]")')

    def test__angular_separation(self) -> None:
        "[test_sql_builder.py] angular_separation: the longitude distance"
        expr = sql_builder.angular_separation(
            sql_builder.column('j2000_longitude', 'obs_ring_geometry'), 30.)
        self.assertEqual(expr.sql,
                         'ABS(MOD(%s - `obs_ring_geometry`.`j2000_longitude`'
                         ' + 540., 360.) - 180.)')
        self.assertEqual(expr.params, [30.])

    def test__aggregates(self) -> None:
        "[test_sql_builder.py] COUNT/SUM/MIN/MAX"
        col = sql_builder.column('size', 'obs_files')
        self.assertEqual(sql_builder.count_star().sql, 'COUNT(*)')
        self.assertEqual(sql_builder.count_distinct(col).sql,
                         'COUNT(DISTINCT `obs_files`.`size`)')
        self.assertEqual(sql_builder.sum_of(col).sql, 'SUM(`obs_files`.`size`)')
        self.assertEqual(sql_builder.min_of(col).sql, 'MIN(`obs_files`.`size`)')
        self.assertEqual(sql_builder.max_of(col).sql, 'MAX(`obs_files`.`size`)')

    def test__join_exprs_is_flat(self) -> None:
        "[test_sql_builder.py] join_exprs: no parentheses are added"
        expr = sql_builder.join_exprs(
            [sql_builder.binary_op(sql_builder.column('a', 't'), '>=',
                                   sql_builder.value(1)),
             sql_builder.binary_op(sql_builder.column('b', 't'), '<=',
                                   sql_builder.value(2))], 'AND')
        self.assertEqual(expr.sql, '`t`.`a` >= %s AND `t`.`b` <= %s')
        self.assertEqual(expr.params, [1, 2])

    def test__join_exprs_rejects_unknown_operator(self) -> None:
        "[test_sql_builder.py] join_exprs: only AND and OR"
        with self.assertRaises(ValueError):
            sql_builder.join_exprs([sql_builder.value(1)], 'XOR')

    def test__combine_exprs_single_is_unparenthesized(self) -> None:
        "[test_sql_builder.py] combine_exprs: one clause is left alone"
        one = sql_builder.binary_op(sql_builder.column('a', 't'), '=',
                                    sql_builder.value(1))
        self.assertEqual(sql_builder.combine_exprs([one], 'OR').sql,
                         '`t`.`a` = %s')

    def test__combine_exprs_multiple_are_parenthesized(self) -> None:
        "[test_sql_builder.py] combine_exprs: more than one clause gets parentheses"
        one = sql_builder.binary_op(sql_builder.column('a', 't'), '=',
                                    sql_builder.value(1))
        two = sql_builder.binary_op(sql_builder.column('b', 't'), '=',
                                    sql_builder.value(2))
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
            'LEFT', 'obs_pds',
            sql_builder.columns_equal(
                sql_builder.column('id', 'obs_general'),
                sql_builder.column('obs_general_id', 'obs_pds')))
        select.add_where(sql_builder.binary_op(
            sql_builder.column('primary_filespec', 'obs_pds'), 'LIKE',
            sql_builder.value('%C11399XX%')))
        select.add_order_by(sql_builder.column('time1', 'obs_general'),
                            descending=False)
        sql, params = select.build()
        self.assertEqual(
            sql,
            'SELECT `obs_general`.`id` FROM `obs_general`'
            ' LEFT JOIN `obs_pds` ON'
            ' `obs_general`.`id`=`obs_pds`.`obs_general_id`'
            ' WHERE `obs_pds`.`primary_filespec` LIKE %s'
            ' ORDER BY `obs_general`.`time1` ASC')
        self.assertEqual(params, ['%C11399XX%'])

    def test__select_params_follow_placeholder_order_not_call_order(self) -> None:
        "[test_sql_builder.py] Select: parameters come out in placeholder order"
        select = sql_builder.Select()
        # Deliberately added back to front: WHERE first, then the join, then the
        # result column, which is the reverse of where they appear in the text.
        select.add_where(sql_builder.binary_op(sql_builder.column('c', 'a'),
                                               '=', sql_builder.value('where')))
        from_source = select.add_from('a')
        from_source.add_join('INNER', 'b',
                             sql_builder.binary_op(sql_builder.column('c', 'b'),
                                                   '=',
                                                   sql_builder.value('join')))
        select.add_column(sql_builder.value('column'))
        sql, params = select.build()
        self.assertEqual(sql,
                         'SELECT %s FROM `a` INNER JOIN `b` ON `b`.`c` = %s'
                         ' WHERE `a`.`c` = %s')
        self.assertEqual(params, ['column', 'join', 'where'])

    def test__select_distinct_hint_group_limit_offset(self) -> None:
        "[test_sql_builder.py] Select: DISTINCT, the optimizer hint, GROUP BY, LIMIT/OFFSET"
        select = sql_builder.Select(distinct=True, max_execution_time=5000)
        select.add_column(sql_builder.column('short_name', 'obs_files'),
                          alias='short')
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
            ' LIMIT 11 OFFSET 20')
        self.assertEqual(params, [])

    def test__select_rejects_non_int_limit_and_offset(self) -> None:
        "[test_sql_builder.py] Select: LIMIT/OFFSET are rendered literally, so they must be ints"
        select = sql_builder.Select()
        with self.assertRaises(ValueError):
            select.limit('10; DROP TABLE obs_general')  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            select.offset('0; DROP TABLE obs_general')  # type: ignore[arg-type]

    def test__select_rejects_non_int_max_execution_time(self) -> None:
        "[test_sql_builder.py] Select: the optimizer hint is rendered literally too"
        with self.assertRaises(ValueError):
            sql_builder.Select(
                max_execution_time='1) */ UNION SELECT 1 /*')  # type: ignore[arg-type]

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
        inner.add_where(sql_builder.binary_op(
            sql_builder.column('session_id', 'cart'), '=',
            sql_builder.value('sess')))

        outer = sql_builder.Select()
        outer.add_column(sql_builder.column('short_name', 't1'))
        outer.add_from(sql_builder.Subquery(inner, 't1'))
        outer.add_from('obs_files')
        outer.add_where(sql_builder.columns_equal(
            sql_builder.column('short_name', 'obs_files'),
            sql_builder.column('short_name', 't1')))
        sql, params = outer.build()
        self.assertEqual(
            sql,
            'SELECT `t1`.`short_name` FROM (SELECT DISTINCT'
            ' `obs_files`.`short_name` FROM `obs_files`'
            ' WHERE `cart`.`session_id` = %s) AS `t1`,`obs_files`'
            ' WHERE `obs_files`.`short_name`=`t1`.`short_name`')
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
                alias='obs_general'))
        sql, _params = select.build()
        self.assertEqual(
            sql,
            'SELECT `obs_general`.`_mult_val_` FROM `obs_general`'
            ' INNER JOIN JSON_TABLE(`obs_general`.`target_name`, "$[*]"'
            ' COLUMNS (`_mult_val_` TEXT PATH "$")) `obs_general`')


class SQLBuilderStatementTests(TestCase):
    """The statements built around a SELECT: INSERT ... SELECT, DELETE and the rest."""

    def test__count_rows(self) -> None:
        "[test_sql_builder.py] count_rows"
        self.assertEqual(sql_builder.count_rows('cache_12'),
                         'SELECT COUNT(*) FROM `cache_12`')

    def test__drop_table(self) -> None:
        "[test_sql_builder.py] drop_table"
        self.assertEqual(sql_builder.drop_table('temp_abc_1_2'),
                         'DROP TABLE `temp_abc_1_2`')

    def test__create_table_as_select_with_column_defs(self) -> None:
        "[test_sql_builder.py] create_table_as_select: the cache-table shape"
        select = sql_builder.Select()
        select.add_column(sql_builder.column('id', 'obs_general'))
        select.add_from('obs_general')
        sql, params = sql_builder.create_table_as_select(
            'cache_12', select,
            column_defs=sql_builder.CACHE_TABLE_COLUMN_DEFS)
        self.assertEqual(
            sql,
            'CREATE TABLE `cache_12`(sort_order INT NOT NULL AUTO_INCREMENT,'
            ' PRIMARY KEY(sort_order), id INT UNSIGNED, UNIQUE KEY(id)) '
            'SELECT `obs_general`.`id` FROM `obs_general`')
        self.assertEqual(params, [])

    def test__create_table_as_select_temporary_without_column_defs(self) -> None:
        "[test_sql_builder.py] create_table_as_select: TEMPORARY, columns from the SELECT"
        select = sql_builder.Select()
        select.add_column(sql_builder.column('sort_order'))
        select.add_from('cache_12')
        select.limit(10)
        select.offset(5)
        sql, _params = sql_builder.create_table_as_select('temp_x', select,
                                                          temporary=True)
        self.assertEqual(
            sql,
            'CREATE TEMPORARY TABLE `temp_x` SELECT `sort_order`'
            ' FROM `cache_12` LIMIT 10 OFFSET 5')

    def test__create_table_from_select_sql(self) -> None:
        "[test_sql_builder.py] create_table_from_select_sql: the pre-rendered SELECT"
        self.assertEqual(
            sql_builder.create_table_from_select_sql('cache_12',
                                                     'SELECT 1'),
            'CREATE TABLE `cache_12` SELECT 1')

    def test__delete_from(self) -> None:
        "[test_sql_builder.py] delete_from"
        sql, params = sql_builder.delete_from(
            'cart',
            sql_builder.binary_op(sql_builder.column('session_id', 'cart'), '=',
                                  sql_builder.value('sess')))
        self.assertEqual(sql,
                         'DELETE FROM `cart` WHERE `cart`.`session_id` = %s')
        self.assertEqual(params, ['sess'])

    def test__delete_joined(self) -> None:
        "[test_sql_builder.py] delete_joined: the rows come from a join"
        from_source = sql_builder.FromSource('cart')
        from_source.add_join(
            'INNER', 'cache_12',
            sql_builder.columns_equal(
                sql_builder.column('id', 'cache_12'),
                sql_builder.column('obs_general_id', 'cart')))
        sql, params = sql_builder.delete_joined(
            'cart', from_source,
            sql_builder.binary_op(sql_builder.column('sort_order', 'cache_12'),
                                  '>=', sql_builder.value(4)))
        self.assertEqual(
            sql,
            'DELETE `cart` FROM `cart` INNER JOIN `cache_12`'
            ' ON `cache_12`.`id`=`cart`.`obs_general_id`'
            ' WHERE `cache_12`.`sort_order` >= %s')
        self.assertEqual(params, [4])

    def test__replace_into_values(self) -> None:
        "[test_sql_builder.py] replace_into_values: one placeholder per column"
        self.assertEqual(
            sql_builder.replace_into_values('cart', ('session_id', 'opus_id')),
            'REPLACE INTO `cart` (`session_id`,`opus_id`) VALUES (%s,%s)')

    def test__replace_into_select(self) -> None:
        "[test_sql_builder.py] replace_into_select"
        select = sql_builder.Select()
        select.add_column(sql_builder.value('sess'))
        select.add_column(sql_builder.column('opus_id', 'obs_general'))
        select.add_from('obs_general')
        sql, params = sql_builder.replace_into_select(
            'cart', ('session_id', 'opus_id'), select)
        self.assertEqual(
            sql,
            'REPLACE INTO `cart` (`session_id`,`opus_id`)'
            ' SELECT %s,`obs_general`.`opus_id` FROM `obs_general`')
        self.assertEqual(params, ['sess'])

    def test__update(self) -> None:
        "[test_sql_builder.py] update: the SET values are parameters too"
        sql, params = sql_builder.update(
            'cart', [('recycled', 0)],
            sql_builder.binary_op(sql_builder.column('session_id', 'cart'), '=',
                                  sql_builder.value('sess')))
        self.assertEqual(
            sql,
            'UPDATE `cart` SET `recycled`=%s WHERE `cart`.`session_id` = %s')
        self.assertEqual(params, [0, 'sess'])
