import pickle
from datetime import datetime

from cat5 import Matchup, MatchupPeriod

if __name__ == "__main__":

    print('--> reading pickles')
    with open('.dev/pickles/demonfb_league.pkl', 'rb') as file:
        league = pickle.load(file)
    with open('.dev/pickles/demonfb_box_scores.pkl', 'rb') as file:
        box_scores = pickle.load(file)

    matchup_period = MatchupPeriod(league)
    now = datetime.now()

    for box in box_scores:
        matchup = Matchup(box, matchup_period, now)
        matchup.home_lineup.set_default()
        matchup.away_lineup.set_default()

        model = matchup.get_model()

        print(matchup)
        print(model.predict_cats())
        print(model.predict_win())
        print()
