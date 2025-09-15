from portfolio_listener import PortfolioListener
from queue import Queue
import time

if __name__ == "__main__":
    # Queue with maxsize=1 means only the latest update is kept
    q = Queue(maxsize=1)
    listener = PortfolioListener(queue=q)
    listener.start()

    try:
        while True:
            df = q.get()  # blocks until a new snapshot arrives
            print("New snapshot received:")
            print(df)
            print("Portfolio PV:", df.attrs.get("portfolio_value"))
    except KeyboardInterrupt:
        listener.stop()
        listener.join()
