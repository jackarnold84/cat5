# CAT5
ESPN Fantasy Basketball H2H Categories Matchup Forecaster

Predict who will win each category

Predict who will win the matchup by winning the most categories. Categories and overall matchups can end in ties.

Forecasts include outright home-win probabilities (`win`, `catWin`) and tie
probabilities (`tie`, `catTie`). Away wins are `1 - home - tie`. Counting
categories model ties explicitly; uncertain FG% and FT% retain a continuous
approximation with zero estimated tie probability, while settled shooting
results can tie. Best lineups maximize the selected team’s outright win chance.

When deploying this change, deploy the processor and refresh stored forecasts
before publishing the UI. Older forecasts display “Tie unavailable” until refreshed.

https://cat5.jarno.site/

## Player projections

Per-game projections retain exponential recency weighting. Cumulative season,
30-day, 15-day, and 7-day stats are split into nonoverlapping groups, so each
observed game contributes once. Counting totals are preferred; per-game
averages multiplied by games played are used when totals are unavailable.
Individual game order is unavailable within each group, so production is
assumed constant inside that group.

The smoothing span is the larger of 30 and the number of observed games. For
fewer than 30 games, a valid preseason per-game projection initializes the
missing history. Without one, smoothing starts from the oldest observed group;
missing data does not insert zero-production games. A player without observed
data uses the preseason projection, or zero if neither is available.

FG% and FT% are projected makes divided by projected attempts, with the same
data and weights used for both counts. Zero attempts produces a zero percentage.
Shooting pairs must be complete and have makes no greater than attempts.
Missing/null stats and invalid numeric inputs are unavailable data, while true
zeros remain observations. Contradictory narrower windows are skipped in favor
of the accepted broader window, allowing only small floating-point differences.

These are calculation and input-handling corrections, not a claim of improved
forecast accuracy. The model still assumes independent Poisson counting totals,
a normal approximation for uncertain shooting percentages, and independent
category outcomes. Changing those assumptions or tuning the recency weights
requires backtesting.


## Service
Deployed to AWS using Lambda, DynamoDB, API Gateway, and EventBridge using SAM.
Both Lambdas are zip packages. The processor zip is built in a Linux ARM64
container so NumPy and SciPy work in Lambda; deployment does not use ECR.

Cloud Infra:

![Cloud Infrastructure](src/images/cat5-infra.png)

### Local Development
Created with python

#### Set up virtual environment:
```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

See [Makefile](Makefile) for dev commands

#### Test:
```sh
make check
make test-unit
make test-integration
make test-cloud-integration
```

#### Build and Deploy:
Requires Docker for the local build, plus AWS CLI and SAM CLI. Deployment
targets `cat5-stack` in `us-east-2` using [samconfig.toml](samconfig.toml).
```sh
make sam
make invoke-processor
make invoke-api
make deploy
```

### Private ESPN league

The processor reads ESPN session cookies from a Systems Manager Parameter
Store `SecureString`. Run `make set-espn-auth` from the repo root to create or
update the parameter. The script prompts without echoing the values, checks
the AWS account, and writes them in `us-east-2`. It stores:

- Name: `/cat5/espn-auth`
- Type: `SecureString` (the default `aws/ssm` key is sufficient)
- Value: `{"espn_s2":"YOUR_ESPN_S2","SWID":"{YOUR_SWID}"}`

To get the values, sign in to ESPN Fantasy in your browser, open developer
tools, and look under Application/Storage → Cookies for `espn_s2` and `SWID`.
Copy their values exactly, including the braces around `SWID`. Treat them as
account credentials. They never belong in Git, a Lambda event, or the browser
site. If ESPN invalidates the session, update this parameter with fresh values.

The `ScheduleDemon` EventBridge rule runs the processor daily at 12:00 UTC.
To refresh the cookies, run `make set-espn-auth` again; no redeploy is needed.
The [2027 event](processor/events/season.json) can also be invoked manually.
The UI checks the forecast's season before displaying it.


## UI
Created with React + Gatsby

See `package.json` for development commands
```sh
npm run start
npm run build
npm run serve
npm run deploy # to GitHub pages
```

Update [`gatsby-config.js`](/gatsby-config.js) for deployment configurations
