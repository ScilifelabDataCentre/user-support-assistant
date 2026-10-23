"""Core of the application: the setup the rest of the code builds on.

  config.py         settings, read from environment variables (dev.env locally)
  clients.py        the shared async API clients (LLM / embedding API, Qdrant)
  logging_setup.py  logging for the whole application, with a request id per line
"""
