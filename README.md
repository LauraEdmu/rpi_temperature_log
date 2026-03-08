# Pi Temperature Logger

Lil python program that stores the current temperature of a Raspberry Pi to a psql database

## Requirements

- Python 3.10+
- PostgreSQL
- Raspberry Pi (or Linux system with `/sys/class/thermal` and `/proc/uptime`)

Install python dependencies:

```bash
pip install -r requirements.txt
````

## Database Setup

Create the database:

```bash
createdb pi_temps
```

The required table will be created automatically when the script runs.

## Configuration

Configuration is provided via environment variables using a `.env` file.

Example `.env`:

```env
DB_USER=your_postgres_user
DB_PASSWORD=your_postgres_password
INTERVAL_SECONDS=30
NUM_OF_INSERTS_PER_COMMIT=5
```

### Variables

| Variable                    | Description                    | Default  |
| --------------------------- | ------------------------------ | -------- |
| `DB_USER`                   | PostgreSQL username            | required |
| `DB_PASSWORD`               | PostgreSQL password            | required |
| `INTERVAL_SECONDS`          | Seconds between measurements   | `30`     |
| `NUM_OF_INSERTS_PER_COMMIT` | Num of inserts between commits | `30`     |

## Running

```bash
python temperature_logger.py
```

The program will:

1. Connect to PostgreSQL
2. Ensure the logging table exists
3. Record temperature and uptime at the configured interval

Stop with:

```
Ctrl+C
```
## Logged Data

Each row contains:

* `recorded_at` — timestamp of the measurement
* `temperature_c` — CPU temperature in Celsius
* `uptime_seconds` — system uptime

Example query:

```sql
SELECT *
FROM cpu_temperature_log
ORDER BY recorded_at DESC
LIMIT 10;
```
