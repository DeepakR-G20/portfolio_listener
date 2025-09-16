import requests
import threading
import time
import logging
from typing import Dict, Any, Optional
import pandas as pd
from queue import Queue, Full
from datetime import datetime

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

API_URL = os.getenv("API_URL", "https://derivalytics.com:666/api/portfolio")
API_PORTFOLIO = os.getenv("API_PORTFOLIO", "*TOTAL_OPTIONS")
API_DETAILED = os.getenv("API_DETAILED", "TRUE")
API_INTERVAL = int(os.getenv("API_INTERVAL", "30"))
GOOGLE_SHEETS_KEY = os.getenv("GOOGLE_SHEETS_KEY", "service_account.json")


class PortfolioListener(threading.Thread):
    def __init__(self, queue: Queue, interval: int = None):
        super().__init__(daemon=True)
        self.interval = interval or API_INTERVAL
        self._stop_event = threading.Event()
        self.queue = queue

        # Logging
        self.logger = logging.getLogger("PortfolioListener")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

        # API params from .env
        self.url = API_URL
        self.params = {
            "portfolio": API_PORTFOLIO,
            "detailed": API_DETAILED,
        }

    def _to_dataframe(self, data: Dict[str, Any]) -> pd.DataFrame:
        """Convert JSON dict from API into a DataFrame with spotrefs as the first column."""
        frames = []
        for key, val in data.items():
            if isinstance(val, dict):
                df = pd.DataFrame.from_dict(val, orient="index", columns=[key])
                frames.append(df)

        if not frames:
            return pd.DataFrame()

        # Combine into one DataFrame
        df = pd.concat(frames, axis=1)

        # Ensure spotrefs is first column
        if "spotrefs" in df.columns:
            cols = ["spotrefs"] + [c for c in df.columns if c != "spotrefs"]
            df = df[cols]

        # Attach metadata
        df.attrs["portfolio_value"] = data.get("pv", None)
        df.attrs["last_published"] = datetime.utcnow().isoformat()  # ISO 8601 UTC timestamp

        return df

    def run(self):
        self.logger.info("Portfolio listener started.")
        while not self._stop_event.is_set():
            try:
                response = requests.get(self.url, params=self.params, timeout=10)
                response.raise_for_status()
                data = response.json()
                df = self._to_dataframe(data)

                # Publish update to queue, overwriting if full
                try:
                    self.queue.put(df, block=False)
                except Full:
                    # Drop the oldest and replace
                    try:
                        self.queue.get_nowait()
                    except Exception:
                        pass
                    self.queue.put_nowait(df)

                self.logger.debug(
                    f"Portfolio updated (PV={df.attrs.get('portfolio_value')}, "
                    f"Last published={df.attrs.get('last_published')})"
                )

            except Exception as e:
                self.logger.error(f"Error fetching portfolio: {e}")

            time.sleep(self.interval)

        self.logger.info("Portfolio listener stopped gracefully.")

    def stop(self):
        self._stop_event.set()
