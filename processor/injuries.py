"""Optional ESPN return estimates, separate from fantasy roster eligibility."""
from datetime import date, datetime, timezone

import requests  # type: ignore[import-untyped]

INJURY_URL = 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/injuries'


def load_return_estimates(league, now=None):
    now = now or datetime.now()
    # The public feed is live, and must never be applied to historical seasons.
    if league.year != now.year + (now.month >= 7):
        return
    try:
        response = requests.get(INJURY_URL, timeout=8)
        response.raise_for_status()
        data = response.json()
        if data.get('season', {}).get('year') != league.year:
            return
        timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
        age = (now.astimezone(timezone.utc) - timestamp).total_seconds()
        if not 0 <= age <= 48 * 3600:
            return
        records = {}
        for team in data.get('injuries', []):
            for injury in team.get('injuries', []):
                athlete = injury.get('athlete', {})
                pid = athlete.get('id')
                # Some ESPN responses supply the ID only inside player links.
                if pid is None:
                    for link in athlete.get('links', []):
                        if '/id/' in link.get('href', ''):
                            pid = link['href'].split('/id/')[1].split('/')[0]
                            break
                if pid is not None:
                    records[str(pid)] = injury
        for team in league.teams:
            for player in team.roster:
                injury = records.get(str(player.playerId), {})
                raw = injury.get('details', {}).get('returnDate')
                try:
                    return_date = date.fromisoformat(raw) if raw else None
                except (TypeError, ValueError):
                    return_date = None
                if return_date and return_date > now.date():
                    player.estimated_return = return_date
                player.injury_note = injury.get('shortComment') or ''
    except (requests.RequestException, ValueError, TypeError, KeyError, AttributeError):
        # Supplemental data must not take down the fantasy forecast.
        print('ESPN return estimates unavailable; using roster injury status')
