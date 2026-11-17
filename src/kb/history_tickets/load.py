"""Load the masked history tickets from an uploaded zip file.

The tickets are masked outside this repo (edge-ticket-exploration, mask_emails.py), which
writes one JSON file per ticket to data/masked_<yyyymmdd-hhmm>/tickets/. That folder is
zipped by hand and uploaded with POST /api/ingestion/tickets (see api/ingestion.py); the
tickets are never stored in this repo.

One masked ticket:
    {"incident_id": "KTH-INC-4492487", "subcategory": "Shiny", "subject": "...",
     "emails": [{"n": 1, "date": "2025-03-02 14:05", "role": "USER", "text": "..."}, ...]}

Loading steps (each function below says which step it implements):

  Step 1. Open the zip from memory (zip_bytes is the content of the uploaded file);
          nothing is written to disk.
  Step 2. Read every .json file in it as one ticket; folders and other files are skipped.
  Step 3. Check every ticket: it must have an incident ID and at least one email.

get_tickets() runs Steps 1-3 and returns the tickets, sorted by file name.
"""

import io
import json
import zipfile


def is_ticket_file(name):
    """Step 2: True for a ticket file in the zip: a .json file that is not a hidden
    file (macOS adds "__MACOSX/._<name>.json" entries to the zips it makes)."""
    file_name = name.split("/")[-1]
    if file_name.startswith("."):
        return False
    return file_name.endswith(".json")


def check_ticket(ticket, name):
    """Step 3: raise ValueError if the ticket has no incident ID or no emails."""
    if not isinstance(ticket, dict):
        raise ValueError(f"{name} is not a ticket (expected a JSON object)")
    if not ticket.get("incident_id"):
        raise ValueError(f"{name} has no incident_id")
    if not ticket.get("emails"):
        raise ValueError(f"{name} has no emails")


def get_tickets(zip_bytes):
    """Run Steps 1-3: return every masked ticket in the uploaded zip (one JSON file per
    ticket), sorted by file name. Raises zipfile.BadZipFile if zip_bytes is not a zip,
    and ValueError if a file is not a valid ticket."""
    tickets = []
    # Step 1. Open the zip from memory
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zip_file:
        for name in sorted(zip_file.namelist()):
            # Step 2. Read every .json file as one ticket
            if not is_ticket_file(name):
                continue
            ticket_text = zip_file.read(name).decode("utf-8")
            ticket = json.loads(ticket_text)

            # Step 3. Check the ticket
            check_ticket(ticket, name)
            tickets.append(ticket)
    return tickets
