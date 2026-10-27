"""guard node of the RAG graph: Step 0 (see the steps in ai_agents/__init__.py).

Rule-based: it blocks the most obvious prompt injection attacks (override the rules,
extract the system prompt, change the assistant's role, chat template tokens) before
any API call. English and Swedish only. Rules catch only the phrasings they list; a
reworded or translated attack gets through, so the system prompt rules still apply
after this node. The rules are kept narrow: a normal question must not be blocked.

One function per step part, then the node that runs them. The node takes the
RagState (state.py) and returns the keys it adds. It only computes (no network).
"""

import logging
import re
import unicodedata

logger = logging.getLogger(__name__)

# The answer to a blocked question (Step 0)
REFUSAL = (
    "I can only answer questions about SciLifeLab Serve. "
    "Please rephrase your question."
)

# Rules matched against the question as typed (casefolded): chat template tokens
# that try to start a fake system / assistant turn. Not XML-like tags such as
# <system>: users paste config files that may contain them (Step 0)
RAW_RULES = [
    ("chat template token",
     re.compile(r"<\|[a-z_]+\|>|\[/?inst\]|<</?sys>>")),
]

# What the assistant is told it now is, in "you are now ..." (Step 0). Not any word:
# "it says you are now logged out" is a normal question
ROLE = (r"(an?\s)?(dan|ai|assistant|chatbot|bot|model|unrestricted|unfiltered"
        r"|uncensored|evil|jailbroken|different|my\s\w+)")
ROLE_SV = (r"(en\s|ett\s)?(dan|ai|assistent|chattbot|bot|modell|obegränsad|ofiltrerad"
           r"|ocensurerad|ond|min\s\w+|mitt\s\w+)")

# Rules matched against the question as words only: casefolded, punctuation replaced
# by single spaces, so "Ignore, all previous... instructions" matches like
# "ignore all previous instructions" (Step 0)
WORD_RULES = [
    # Override the rules
    ("override instructions",
     re.compile(r"\b(ignore|disregard|forget|override|bypass)\s(\w+\s){0,3}"
                r"(previous|prior|above|earlier|preceding|system|initial|original|your)\s"
                r"(\w+\s)?(instructions?|rules|prompts?|guidelines|directions)\b")),
    ("forget everything",
     re.compile(r"\b(ignore|disregard|forget)\s(all|everything)\s"
                r"(above|before|you\swere\stold)\b")),
    # Extract the system prompt
    ("your system prompt",
     re.compile(r"\byour\s(system|initial|original|hidden|secret|full)\s"
                r"(prompt|instructions?|message|rules)\b")),
    ("reveal system prompt",
     re.compile(r"\b(reveal|show|print|repeat|output|display|leak|dump|recite)\s(\w+\s){0,4}"
                r"(system|initial|hidden|secret)\s(prompt|instructions?|message)\b")),
    ("repeat text above",
     re.compile(r"\b(repeat|print|output|recite|reveal|show)\s(\w+\s){0,4}"
                r"(text|words|everything|instructions?|content)\s(above|before)\b")),
    # Change the assistant's role
    ("role override",
     re.compile(r"\b((you\s(are|re)\snow|from\snow\son\syou\s(are|re))\s" + ROLE +
                r"|you\s(are|re)\sno\slonger\s(an?\s)?(ai|assistant|bound|restricted|limited)"
                r"|from\snow\son\syou\s(will|must|shall|should)\s(\w+\s){0,2}"
                r"(answer|respond|reply|act|behave|ignore|pretend|roleplay|only)"
                r"|act\sas\sif\syou|roleplay\sas|do\sanything\snow"
                r"|jailbreak\s(mode|yourself))\b")),
    # "pretend to be" only as a command: "can my app pretend to be a browser" is normal
    ("pretend",
     re.compile(r"(^|\b(you|please|now|and)\s)pretend\sto\sbe\b"
                r"|\bpretend\s(that\s)?you\s(are|re)\b")),
    # Not "developer mode" alone: "is there a developer mode for Serve apps" is normal
    ("developer mode",
     re.compile(r"\b(you\s(are|re)\s(now\s)?in|enter|simulate)\sdeveloper\smode\b")),
    # Swedish: the same attacks; nouns end in \w* for the definite and plural forms
    # (instruktionerna, reglerna, systemprompten)
    ("override instructions (sv)",
     re.compile(r"\b(ignorera|strunta\si|glöm|bortse\sfrån|åsidosätt)\s(\w+\s){0,3}"
                r"(tidigare|föregående|ovanstående|ursprungliga|dina|system)\s"
                r"(\w+\s)?(instruktion\w*|regler\w*|prompt\w*|riktlinje\w*|direktiv\w*)\b")),
    ("forget everything (sv)",
     re.compile(r"\b(ignorera|strunta\si|glöm|bortse\sfrån)\s"
                r"(allt|alla|instruktionerna|reglerna)\s"
                r"(ovan|ovanför|innan|du\s(har\s)?fått)\b")),
    ("your system prompt (sv)",
     re.compile(r"\b(din|dina)\s(systemprompt\w*|systeminstruktion\w*|systemmeddelande\w*"
                r"|(ursprungliga|dolda|hemliga|initiala|interna)\s"
                r"(prompt\w*|instruktion\w*|regler\w*))\b")),
    # No "visa" (show): "visa systemmeddelandet i min app" is a normal question
    ("reveal system prompt (sv)",
     re.compile(r"\b(avslöja|upprepa|skriv\sut|återge|citera|läck)\s(\w+\s){0,4}"
                r"(systemprompt\w*|systeminstruktion\w*|systemmeddelande\w*"
                r"|(dolda|hemliga|ursprungliga)\sinstruktion\w*)\b")),
    ("repeat text above (sv)",
     re.compile(r"\b(upprepa|skriv\sut|återge|citera)\s(\w+\s){0,4}"
                r"(texten|orden|allt|instruktionerna|innehållet)\s(ovan|ovanför|innan|före)\b")),
    ("role override (sv)",
     re.compile(r"\b((du\sär\snu|från\soch\smed\snu\sär\sdu)\s" + ROLE_SV +
                r"|du\sär\sinte\slängre\s(en\s)?(ai|assistent|begränsad|bunden)"
                r"|från\soch\smed\snu\s(ska|måste|kommer)\sdu\s(\w+\s){0,2}"
                r"(svara|agera|bete|ignorera|låtsas|spela|bara)"
                r"|spela\srollen\som|agera\ssom\som\sdu)\b")),
    ("pretend (sv)",
     re.compile(r"(^|\b(du|nu|och|snälla)\s)låtsas\svara\b"
                r"|\blåtsas\satt\sdu\sär\b")),
    ("developer mode (sv)",
     re.compile(r"\b(du\sär\s(nu\s)?i|gå\sin\si|simulera)\sutvecklarläge\w*")),
]

# A match is not an attack when the user is the subject: "can I ignore the previous
# instructions", "how do I show the system message", "kan jag ignorera ...".
# Matched against the text before the match (Step 0)
USER_SUBJECT_RE = re.compile(
    r"\b(i|we|jag|vi)\s((can|could|should|must|may|might|will|would|need\sto"
    r"|have\sto|want\sto|kan|ska|bör|måste|vill|behöver|får|borde|skulle|kunde)\s)*$"
)

# Nor when it is about the user's own app or the docs: "show the system message in
# my app", "ignore the previous instructions in the docs". Matched against the text
# after the match (Step 0)
OWN_CONTEXT_RE = re.compile(
    r"^(\s\w+){0,2}\s(in|of|for|from|on|i|för|från|på|av)\s"
    r"(my|our|the\sdocs|the\sdocumentation|min|mitt|mina|vår|vårt|våra|dokumentationen)\b"
)

# Anything that is not a letter or digit: replaced by a space in the words text (Step 0)
NON_WORD_RE = re.compile(r"[\W_]+")


# --------------------------- Step 0: check the question ----------------------

def normalize_question(question):
    """Step 0: return (raw_text, word_text): the question in NFKC, casefolded, without
    invisible characters (zero-width spaces etc. can split a keyword); and the same
    text as words only, separated by single spaces."""
    text = unicodedata.normalize("NFKC", question).casefold()
    kept = []
    for char in text:
        # Cf: format characters, e.g. zero-width space / joiner, soft hyphen
        if unicodedata.category(char) == "Cf":
            continue
        kept.append(char)
    raw_text = "".join(kept)
    word_text = NON_WORD_RE.sub(" ", raw_text).strip()
    return raw_text, word_text


def is_normal_use(word_text, match):
    """Step 0: True if a word rule match is a normal question, not an attack: the user
    is the subject, or it is about the user's own app or the docs."""
    before = word_text[:match.start()]
    after = word_text[match.end():]
    if USER_SUBJECT_RE.search(before):
        return True
    if OWN_CONTEXT_RE.search(after):
        return True
    return False


def find_injection(raw_text, word_text):
    """Step 0: the first rule the question matches, as (rule name, matched text);
    None when it matches none. Word rule matches that are normal use are skipped."""
    for name, pattern in RAW_RULES:
        match = pattern.search(raw_text)
        if match:
            return name, match.group(0)
    for name, pattern in WORD_RULES:
        for match in pattern.finditer(word_text):
            if is_normal_use(word_text, match):
                logger.info("Rule %r matched %r, but as normal use", name, match.group(0))
                continue
            return name, match.group(0)
    return None


# ------------------------------------ Node -----------------------------------

def guard(state):
    """Node: Step 0, block the question if it matches a prompt injection rule; the
    graph then ends with the refusal (see graph/rag_graph.py)."""
    logger.info("Step 0: check the question for prompt injection")
    raw_text, word_text = normalize_question(state["question"])
    found = find_injection(raw_text, word_text)
    if found is None:
        return {"blocked": False}

    name, matched = found
    logger.warning("Question blocked: prompt injection rule %r matched %r", name, matched)
    return {"blocked": True, "answer": REFUSAL, "sources": []}
