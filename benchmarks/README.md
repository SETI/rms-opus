# The benchmark harness

How to run it, read a result, take an A/B and keep the measuring machine idle is
`docs/dev_guide_benchmarks.rst` (rendered at
<https://rms-opus.readthedocs.io/en/latest/dev_guide_benchmarks.html>). This file holds
the one thing the guide points here for: the MySQL tuning baseline.

## The MySQL tuning baseline

The harness-owned server runs `scenarios/my.cnf.template`, filled in by
`bench_server.py` from `scenarios/server.toml`. Results are judged against each other,
not against this baseline; it exists so that every result is measured on a server
configured by stated rules rather than by MySQL's defaults for a small machine.

The rules that MySQL's documentation gives in terms of the machine's memory are applied
to `memory_budget_gb` in `server.toml` rather than to the machine's total, because the
measuring machine runs other work too. With the budget at 24 GiB the server gets an 18
GiB buffer pool and a 14 GiB redo log; `tests/benchmarks/test_bench_server.py` checks
one budget in each band of the documented tables.

| Setting | Value | Rule | Source |
| --- | --- | --- | --- |
| `innodb_buffer_pool_size` | 128 MiB below 1 GiB of budget, half the budget up to 4 GiB, three quarters above, in whole chunks | `innodb_dedicated_server`'s automatic buffer pool size | [17.8.12 Enabling Automatic InnoDB Configuration for a Dedicated MySQL Server](https://dev.mysql.com/doc/refman/8.0/en/innodb-dedicated-server.html), Table 17.8 |
| `innodb_buffer_pool_chunk_size` | 128 MiB | The default; the pool must be a multiple of the chunk size times the instances | [17.8.3.1 Configuring InnoDB Buffer Pool Size](https://dev.mysql.com/doc/refman/8.0/en/innodb-buffer-pool-resize.html) |
| `innodb_buffer_pool_instances` | 1 | One pool, so the cold-start state is one thing | [17.8.3.1](https://dev.mysql.com/doc/refman/8.0/en/innodb-buffer-pool-resize.html) |
| `innodb_redo_log_capacity` | 100 MiB up to 2 GiB of budget; `round(0.5 × GB) × 0.5` GiB up to 4; `round(0.75 × GB) × 0.5` GiB up to 10.66; `round(0.5625 × GB)` GiB up to 170.66; 128 GiB above | `innodb_dedicated_server`'s automatic redo log capacity (8.0.30 and later) | [17.8.12](https://dev.mysql.com/doc/refman/8.0/en/innodb-dedicated-server.html), Table 17.9 |
| `innodb_flush_method` | `O_DIRECT` | No reads through the operating system's page cache, so a restart is a cold start | [InnoDB Startup Options and System Variables](https://dev.mysql.com/doc/refman/8.0/en/innodb-parameters.html#sysvar_innodb_flush_method) |
| `innodb_io_capacity` | 1000 | The documentation's figure for a higher-end, bus-attached SSD | [17.8.7 Configuring InnoDB I/O Capacity](https://dev.mysql.com/doc/refman/8.0/en/innodb-configuring-io-capacity.html) |
| `innodb_io_capacity_max` | 2000 | Twice `innodb_io_capacity`, the documentation's starting point | [17.8.7](https://dev.mysql.com/doc/refman/8.0/en/innodb-configuring-io-capacity.html) |
| `sort_buffer_size` | 256 KiB | The default | [Server System Variables](https://dev.mysql.com/doc/refman/8.0/en/server-system-variables.html#sysvar_sort_buffer_size) |
| `tmp_table_size` | 16 MiB | The default | [Server System Variables](https://dev.mysql.com/doc/refman/8.0/en/server-system-variables.html#sysvar_tmp_table_size) |
| `temptable_max_ram` | 1 GiB | The default | [Server System Variables](https://dev.mysql.com/doc/refman/8.0/en/server-system-variables.html#sysvar_temptable_max_ram) |
| `local_infile` | `ON` | A bulk loader may use `LOAD DATA LOCAL INFILE` | [Server System Variables](https://dev.mysql.com/doc/refman/8.0/en/server-system-variables.html#sysvar_local_infile) |
| `skip-log-bin` | set | No binary log; `log_bin = OFF` would instead name a log file `OFF` | [Binary Logging Options and Variables](https://dev.mysql.com/doc/refman/8.0/en/replication-options-binary-log.html) |
| `max_digest_length` | 4096 | Long enough that wide search statements keep distinct digests | [Server System Variables](https://dev.mysql.com/doc/refman/8.0/en/server-system-variables.html#sysvar_max_digest_length) |
| `performance_schema_max_digest_length` | 4096 | The same for the Performance Schema; capped by `max_digest_length` | [Performance Schema System Variables](https://dev.mysql.com/doc/refman/8.0/en/performance-schema-system-variables.html#sysvar_performance_schema_max_digest_length) |
| `innodb_buffer_pool_load_at_startup`, `innodb_buffer_pool_dump_at_shutdown` | `OFF` | No buffer pool carried across a restart | [17.8.3.6 Saving and Restoring the Buffer Pool State](https://dev.mysql.com/doc/refman/8.0/en/innodb-preload-buffer-pool.html) |

Every other setting is the server's default, and every result records the values the
running server reports for the settings above and a few more (`RECORDED_SETTINGS` in
`bench_server.py`).
