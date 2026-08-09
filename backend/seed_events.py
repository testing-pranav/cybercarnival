"""
One-time seed: populates data/events.json with the same 11 events currently
shown on the frontend (lib/events-data.ts), so the registration API and
admin panel have real event_ids to work with from day one.

Safe to re-run: skips any event whose name already exists.
Run: python seed_events.py
"""
from services.event_service import list_events, create_event

EVENTS = [
    {"name": "CAPTURE THE FLAG", "fee": "₹250 PER TEAM", "team_size": "TBA", "venue": "SRM RAMAPURAM", "date": "7 — 8 OCTOBER"},
    {"name": "BUG BOUNTY", "fee": "₹200 PER TEAM", "team_size": "2 MEMBERS", "venue": "SRM RAMAPURAM", "date": "7 — 8 OCTOBER"},
    {"name": "RED TEAM × BLUE TEAM", "fee": "₹250 PER TEAM", "team_size": "TBA", "venue": "SRM RAMAPURAM", "date": "7 — 8 OCTOBER"},
    {"name": "PAPER PRESENTATION", "fee": "TBA", "team_size": "TBA", "venue": "SRM RAMAPURAM", "date": "7 — 8 OCTOBER"},
    {"name": "CYBER CONCLAVE", "fee": "TBA", "team_size": "TBA", "venue": "SRM RAMAPURAM", "date": "7 — 8 OCTOBER"},
    {"name": "TOOL EXPO", "fee": "₹250 PER TEAM", "team_size": "TBA", "venue": "SRM RAMAPURAM", "date": "7 — 8 OCTOBER"},
    {"name": "WORKSHOPS", "fee": "TBA", "team_size": "TBA", "venue": "SRM RAMAPURAM", "date": "7 OCTOBER"},
    {"name": "SHARK TANK", "fee": "₹250 PER TEAM", "team_size": "TBA", "venue": "SRM RAMAPURAM", "date": "7 — 8 OCTOBER"},
    {"name": "SHIPWRECK", "fee": "₹200 PER TEAM", "team_size": "1 — 2 MEMBERS", "venue": "SRM RAMAPURAM", "date": "7 — 8 OCTOBER"},
    {"name": "BEHIND THE CRIME", "fee": "₹250 PER TEAM", "team_size": "TBA", "venue": "SRM", "date": "7 OCTOBER"},
    {"name": "CYBER AWARENESS RALLY", "fee": "TBA", "team_size": "TBA", "venue": "TBA", "date": "7 — 8 OCTOBER"},
]

if __name__ == "__main__":
    existing_names = {e["name"] for e in list_events()}
    created = 0
    for e in EVENTS:
        if e["name"] in existing_names:
            continue
        create_event(e)
        created += 1
    print(f"Seeded {created} new event(s). {len(list_events())} total in data/events.json")
