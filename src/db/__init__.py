"""Persistent storage in Postgres: one module per table, with its SQL functions.

  schema.sql            the tables, created at startup (see app.py)
  support_requests.py   create_table(), save_request()

The connection pool is created in core/clients.py and opened in app.py's lifespan;
the functions here take it as their first argument.
"""
