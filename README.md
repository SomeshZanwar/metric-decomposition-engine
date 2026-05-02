# Metric Decomposition Engine

An automated system that investigates why a metric changed — breaking down the movement across dimensions, ranking root causes by impact, and generating plain-English incident reports.

This solves the most common ad-hoc request product analysts get: "DAU dropped 12% on Monday — why?"

Instead of spending hours slicing data manually, this engine runs the investigation automatically and outputs a stakeholder-ready report in seconds.

## What It Does

1. Takes any event-based metric (e.g., PushEvents, PullRequestEvents) across two time periods
2. Decomposes the change across multiple dimensions (actor, repository, organization)
3. Ranks each segment's contribution to the total change
4. Generates a plain-English incident report with executive summary, dimensional breakdowns, root cause hypothesis, and recommended next steps
5. Provides an interactive Streamlit dashboard for running decompositions on demand

## Example Output

METRIC CHANGE INCIDENT REPORT

EXECUTIVE SUMMARY
Count of PushEvent decreased by 4.2% (382,104 → 366,058, change of -16,046)
between 2024-01-15 and 2024-01-22.

BREAKDOWN BY: repo_name
The largest contributor was 'example/repo' with a decrease of 1,203 events
(7.5% of total change).

ROOT CAUSE HYPOTHESIS
The primary driver of this metric change appears to be 'example/repo'
(dimension: repo_name), accounting for 7.5% of the total change.

*(Numbers above are illustrative. Actual output depends on the data loaded.)*

## Tech Stack

- **Python** — core decomposition logic, data pipeline, report generation
- **PostgreSQL** — event storage and dimensional queries
- **pandas** — data manipulation and aggregation
- **SQLAlchemy** — database connectivity
- **Streamlit** — interactive dashboard UI
- **Jinja2** — report templating

## Project Structure

metric-decomposition-engine/
├── data/
│   └── raw/                  # GitHub Archive .json.gz files (gitignored)
├── notebooks/                # Exploratory analysis
├── src/
│   ├── load_gharchive.py     # Data pipeline: GH Archive → PostgreSQL
│   ├── decompose.py          # Core decomposition engine
│   ├── report_generator.py   # Plain-English report builder
│   └── app.py                # Streamlit dashboard
├── reports/                  # Generated incident reports
├── tests/
├── .env                      # Database config (gitignored)
├── .gitignore
├── requirements.txt
└── README.md

## Setup

### Prerequisites

- Python 3.9+
- PostgreSQL
- Git

### Installation

1. Clone the repository:
```bash
   git clone https://github.com/SomeshZanwar/metric-decomposition-engine.git
   cd metric-decomposition-engine
```

2. Create and activate a virtual environment:
```bash
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # Mac/Linux
```

3. Install dependencies:
```bash
   pip install -r requirements.txt
```

4. Create a PostgreSQL database:
```sql
   CREATE DATABASE metric_decomposition;
```

5. Create a `.env` file in the project root:
DB_HOST=localhost
DB_PORT=5432
DB_NAME=metric_decomposition
DB_USER=postgres
DB_PASSWORD=your_password

6. Download GitHub Archive data:
```bash
   cd data/raw
   curl -L -O https://data.gharchive.org/2024-01-15-0.json.gz
   curl -L -O https://data.gharchive.org/2024-01-22-0.json.gz
   cd ../..
```

7. Load data into PostgreSQL:
```bash
   python src/load_gharchive.py
```

## Usage

### Run decomposition from command line:
```bash
python src/decompose.py
```

### Generate an incident report:
```bash
python src/report_generator.py
```

### Launch the interactive dashboard:
```bash
cd src
streamlit run app.py
```

## How the Decomposition Works

The engine uses a dimensional drilldown approach:

1. **Baseline vs Comparison**: Counts the target metric for each time period
2. **Dimensional Split**: Groups the metric by each dimension (actor, repo, org)
3. **Segment Change**: Calculates the absolute change per segment between periods
4. **Contribution Ranking**: Expresses each segment's change as a percentage of the total change
5. **Root Cause Hypothesis**: Identifies the dimension and segment with the highest absolute contribution

This mirrors how internal analytics tools at companies like Meta, Uber, and Airbnb investigate metric movements — except packaged as a reusable, open-source system.

## Dataset

Uses [GitHub Archive](https://www.gharchive.org/) — a public dataset that records every event on public GitHub repositories (pushes, pull requests, issues, forks, stars) with hourly granularity since 2011.

This dataset was chosen over synthetic data because:
- Real-world scale and messiness
- Known events (GitHub outages, feature launches) serve as natural test cases for the decomposition
- Multiple natural dimensions for drilldown (user, repo, org, event type)

## What I Learned

- Metric decomposition is conceptually simple but operationally tricky — edge cases like segments that appear in only one period, or dimensions with high cardinality, required careful handling
- The report generator taught me that the hardest part of analytics is not the calculation — it is translating the result into something a non-technical stakeholder can act on
- Building the Streamlit layer showed how much difference interactivity makes when the same analysis exists as a script vs. a tool someone can actually use

## Future Improvements

- Add time-series decomposition (not just two-point comparison)
- Support for custom SQL-defined metrics beyond event counts
- Statistical significance testing for segment-level changes
- Automated anomaly detection to trigger decompositions without manual date selection
- OpenAI API integration for more nuanced natural-language summaries