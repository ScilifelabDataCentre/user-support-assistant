"""Turn the masked history tickets into chunks for the knowledge base.

One ticket = one chunk. The ticket is written as one text: a header with the ticket ID,
subcategory and subject, then every email in order, each starting with a label line
that says who sent it and when:

    Ticket: KTH-INC-4492487 | Subcategory: Shiny
    Subject: App fails to start after update

    [Email 1 | User | 2025-03-02 14:05]
    My app shows "Error: port 3838 not responding" after I pushed the new image...

    [Email 2 | Support | 2025-03-03 09:12]
    Could you check that your Dockerfile exposes port 3838? ...

Chunking steps (each function below says which step it implements):

  Step 1. Header: the ticket ID + subcategory, and the subject (a missing subcategory
          or subject is left out).
  Step 2. Emails: every email as a block: the label line
          "[Email n | User/Support | yyyy-mm-dd hh:mm]", then its text. User/Support
          comes from the email's "role".
  Step 3. Join: the header and the email blocks in email order (n), separated by blank
          lines.
  Step 4. Build the chunk, with the same keys the docs chunks use (serve_docs/chunk.py),
          so embed.py and deploy.py take it as is:
            "id":      stable id made from the incident ID, so a rebuild gives the same id
            "text":    what is embedded and indexed for BM25: the ticket text, cut at
                       MAX_EMBED_CHARS
            "content": the whole ticket text, given to the LLM as context
          and metadata about the ticket, for filtering and display.

chunk_tickets() applies Steps 1-4 to all tickets and returns one list of chunks.

Not done yet: removing greetings and signatures, and splitting long tickets into
several chunks.
"""

import uuid

# Longest text sent to the embedding model, in characters. The model (bge-m3) takes 8192
# tokens and refuses longer texts. 20,000 characters is under that for normal text, but
# not always for logs, code and URLs; embed.py shortens a text the model still refuses.
MAX_EMBED_CHARS = 20000

# Role of an email in the masked tickets -> its label in the text (Step 2)
ROLE_LABELS = {"USER": "User", "SUPPORT": "Support"}


# ------------------------------- Step 1: header ------------------------------

def get_subcategory(ticket):
    """Step 1: return the ticket's subcategory, or None if it has none (NaN in the export)."""
    value = ticket.get("subcategory")
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def get_subject(ticket):
    """Step 1: return the ticket's subject, or "" if it has none."""
    return (ticket.get("subject") or "").strip()


def format_header(ticket):
    """Step 1: return the header lines:
        Ticket: KTH-INC-4492487 | Subcategory: Shiny
        Subject: App fails to start after update
    A missing subcategory or subject is left out."""
    first_line = f"Ticket: {ticket['incident_id']}"
    subcategory = get_subcategory(ticket)
    if subcategory:
        first_line += f" | Subcategory: {subcategory}"
    lines = [first_line]

    subject = get_subject(ticket)
    if subject:
        lines.append(f"Subject: {subject}")
    return "\n".join(lines)


# ------------------------------- Step 2: emails ------------------------------

def get_emails(ticket):
    """Step 2: return the ticket's emails in email order (n)."""
    return sorted(ticket["emails"], key=lambda email: email["n"])


def format_email(email):
    """Step 2: return one email as a block: the label line
        [Email 2 | Support | 2025-03-03 09:12]
    then its text. The date is already stored as yyyy-mm-dd hh:mm."""
    role = ROLE_LABELS[email["role"]]
    label = f"[Email {email['n']} | {role} | {email['date']}]"
    return f"{label}\n{email['text'].strip()}"


# -------------------------------- Step 3: join -------------------------------

def format_ticket(ticket):
    """Steps 1-3: return the whole ticket as one text: the header, then every email
    block in email order (n), separated by blank lines."""
    # Step 1. Header
    blocks = [format_header(ticket)]
    # Step 2. One block per email, in email order
    for email in get_emails(ticket):
        blocks.append(format_email(email))
    # Step 3. Join, separated by blank lines
    return "\n\n".join(blocks)


# ---------------------------- Step 4: build the chunk ------------------------

def count_role(emails, role):
    """Step 4: return how many of the emails have the given role ("USER" or "SUPPORT")."""
    count = 0
    for email in emails:
        if email["role"] == role:
            count += 1
    return count


def chunk_ticket(ticket):
    """Apply Steps 1-4 to one masked ticket and return its chunk."""
    # Steps 1-3. The ticket as one text
    content = format_ticket(ticket)

    # Step 4. Build the chunk
    emails = get_emails(ticket)
    return {
        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, f"ticket:{ticket['incident_id']}")),
        "source": "history_tickets",
        "incident_id": ticket["incident_id"],
        "subcategory": get_subcategory(ticket),
        "subject": get_subject(ticket),
        "first_date": emails[0]["date"],
        "last_date": emails[-1]["date"],
        "n_emails": len(emails),
        "n_user_emails": count_role(emails, "USER"),
        "n_support_emails": count_role(emails, "SUPPORT"),
        "n_chars": len(content),
        "truncated": len(content) > MAX_EMBED_CHARS,
        "content": content,
        "text": content[:MAX_EMBED_CHARS],
    }


# --------------------------------- pipeline ----------------------------------

def chunk_tickets(tickets):
    """Apply Steps 1-4 to every masked ticket and return all chunks in one list."""
    chunks = []
    for ticket in tickets:
        chunk = chunk_ticket(ticket)
        chunks.append(chunk)
    return chunks
