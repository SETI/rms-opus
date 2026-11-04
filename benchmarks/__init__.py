"""The benchmark harness: import, database and web measurements on a harness-owned server.

Run from a checkout's root, as ``python -m benchmarks.<command>``. The commands are
`benchmarks.bench_server` (the MySQL server, memcached and gunicorn the harness owns),
`benchmarks.bench_import`, `benchmarks.bench_db`, `benchmarks.bench_web`, and
`benchmarks.compare`. Every measurement lands in a result file under
``benchmarks/results/``; raw logs, profiles and query captures go under
``benchmarks/scratch/``, which is not committed. ``docs/dev_guide_benchmarks.rst`` is the
guide.
"""
