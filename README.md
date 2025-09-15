Portfolio Listener

A lightweight, thread-based service that polls the Derivalytics Portfolio API on a configurable interval, converts the JSON response into a pandas DataFrame, and publishes updates into a thread-safe queue for consumption by trading infrastructure.


Features

Polls portfolio data from Derivalytics API (https://derivalytics.com:666/api/portfolio)

Interval, URL, and parameters configurable via .env file

Converts JSON snapshots into clean tabular format with pandas.DataFrame

Publishes updates into a bounded queue.Queue (thread-safe)

Graceful startup/shutdown using threading.Thread

Logging with timestamps and error handling


Requirements

Python 3.10+

Conda or virtualenv recommended

Dependencies (installed via environment.yml or pip):

requests

pandas

python-dotenv


Setup

Clone the repo

git clone https://github.com/DeepakR-G20/portfolio_listener.git
cd portfolio_listener


Create environment

conda env create -f environment.yml
conda activate portfolio-listener


Create .env file in project root:

API_URL=https://derivalytics.com:666/api/portfolio
API_PORTFOLIO=*TOTAL_OPTIONS
API_DETAILED=TRUE
API_INTERVAL=30


Usage

Run the listener:

python main.py

Example output
2025-09-15 13:00:00 [INFO] PortfolioListener: Portfolio listener started.
New snapshot received:
              deltas     delta_usds   gammas ...
AVAXUSD   3348.386688  95763.859269  5696.2851 ...
BTCUSD      -0.114194 -13118.293301     0.3084 ...
...
Portfolio PV: 3159090.904025922

Architecture

PortfolioListener (thread)

Fetches data from API on interval

Converts JSON → DataFrame

Pushes latest snapshot into queue (drops oldest if queue full)

Main consumer loop

Calls q.get() to block until a new snapshot arrives

Prints or processes the DataFrame

Customization

Change polling interval or API params by editing .env.

Adjust queue size in main.py:

q = Queue(maxsize=5)  # keep up to 5 snapshots


Integrate into larger trading app by having other threads consume the queue.

Graceful Shutdown

Press Ctrl+C:

Signals PortfolioListener to stop

Joins thread to ensure clean exit
