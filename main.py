import os # for os.getenv() and os.environ.get()
import time
from datetime import datetime, timezone
from dotenv import load_dotenv
import psycopg
import logging

load_dotenv() 

# --- Logging setup ---
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s"
)

# stdout handler (INFO and above)
stdout_handler = logging.StreamHandler()
stdout_handler.setLevel(logging.INFO)
stdout_handler.setFormatter(formatter)

# file handler (WARN and above)
file_handler = logging.FileHandler("temperature_log.log")
file_handler.setLevel(logging.WARNING)
file_handler.setFormatter(formatter)

if not logger.handlers:
    logger.addHandler(stdout_handler)
    logger.addHandler(file_handler)

# --- Configuration ---

db_user = os.getenv("DB_USER")
if not db_user:
    logger.error("DB_USER environment variable not set")
    raise ValueError("DB_USER environment variable not set")
db_password = os.getenv("DB_PASSWORD")
if not db_password:
    logger.error("DB_PASSWORD environment variable not set")
    raise ValueError("DB_PASSWORD environment variable not set")

DB_CONFIG = {
    "dbname": "pi_temps",
    "user": db_user,
    "password": db_password,
    "host": "localhost",
    "port": 5432,
}

INTERVAL_SECONDS_STR:str = os.getenv("INTERVAL_SECONDS", "30")
try:    INTERVAL_SECONDS:int = int(INTERVAL_SECONDS_STR)
except ValueError:
    logger.error("INTERVAL_SECONDS environment variable must be an integer")
    raise ValueError("INTERVAL_SECONDS environment variable must be an integer")
if INTERVAL_SECONDS <= 0:
    logger.error("INTERVAL_SECONDS must be a positive integer")
    raise ValueError("INTERVAL_SECONDS must be a positive integer")

def get_cpu_temp_c() -> float:
    with open("/sys/class/thermal/thermal_zone0/temp", "r", encoding="utf-8") as f:
        temp_str = f.read().strip()

    try:
        return int(temp_str) / 1000.0
    except ValueError as e:
        logger.error("Failed to read CPU temperature - invalid value: %r", temp_str)
        raise ValueError("Failed to parse CPU temperature") from e

def get_uptime_seconds() -> float:
    with open("/proc/uptime", "r", encoding="utf-8") as f:
        return float(f.read().split()[0])

def ensure_table(conn: psycopg.Connection) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS cpu_temperature_log (
                id BIGSERIAL PRIMARY KEY,
                recorded_at TIMESTAMPTZ NOT NULL,
                temperature_c DOUBLE PRECISION NOT NULL,
                uptime_seconds BIGINT NOT NULL
            );
            """
        )
    conn.commit()

def log_temperature(conn: psycopg.Connection, temperature_c: float, uptime_seconds: float) -> None:
    now = datetime.now(timezone.utc)
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO cpu_temperature_log (recorded_at, temperature_c, uptime_seconds)
            VALUES (%s, %s, %s);
            """,
            (now, temperature_c, int(uptime_seconds)),
        )

def main() -> None:
    logger.info("Connecting to PostgreSQL...")
    NUM_OF_INSERTS_PER_COMMIT = int(os.getenv("NUM_OF_INSERTS_PER_COMMIT", "5"))
    insert_counter = 0
    
    with psycopg.connect(**DB_CONFIG) as conn:
        ensure_table(conn)
        logger.info("Logging started. Press Ctrl+C to stop.")

        try:
            while True:
                temp_c = get_cpu_temp_c()
                uptime_seconds = get_uptime_seconds()
                log_temperature(conn, temp_c, uptime_seconds)
                logger.debug(f"{datetime.now().isoformat(timespec='seconds')}  {temp_c:.1f} °C  Uptime: {uptime_seconds:.0f} seconds")
                insert_counter += 1
                if insert_counter >= NUM_OF_INSERTS_PER_COMMIT:
                    conn.commit()
                    insert_counter = 0
                time.sleep(INTERVAL_SECONDS)
        except KeyboardInterrupt:
            logger.info("Logging stopped by user.")
        finally:
            if insert_counter > 0:
                conn.commit()
                logger.info("Committed remaining entries before exit.")


if __name__ == "__main__":
    main()