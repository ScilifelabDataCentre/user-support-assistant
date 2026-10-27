"""Nodes of the RAG graph: one file per node, holding its step functions.

  guard.py            guard: Step 0, block prompt injection with rules
  retrieve.py         retrieve: Steps 1-3, find the chunks for the question
  generate_answer.py  generate_answer: Steps 4-6, answer from the chunks, with sources
"""
