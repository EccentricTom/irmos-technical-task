# Midspan Data API Takehome Task

FastAPI service for loading bridge data into SQLite and serving processed time-series data for visualization.

## What this project does

- Reads bridge data from a SQLite database (`midspan_data.db`)
- Exposes an API endpoint to return:
  - raw data, or
  - processed data (outlier handling → downsampling → smoothing)
- Supports local development and Docker/Compose workflows

---

## Project Structure

```text
.
├── README.md
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── uv.lock
├── requirements.txt
├── pytest.ini
├── main.py
├── db_accs.py
├── test_script.py
├── api/
│   ├── app.py
│   └── settings.py
└── data/
    ├── load_csv_to_db.py
    ├── midspan_data.csv
    └── midspan_data.db
```

## Environment variables

create a .env file in the root folder with the following variables (change according to where you save the CSV file etc.)

```text
DB_URL=sqlite:///./data/midspan_data.db
CSV_PATH=./data/midspan_data.csv
TABLE_NAME=midspan_data
MODE_DB=replace
ENABLE_DEBUG_ENDPOINT=true
```

Note: When the Docker container runs, the `DB_URL / CSV_PATH` are overriden for container-safe paths, remember to adjust these if the CSV file and DB url are different in your run.

## Run with Docker compose (Recommended)

### 1) Build images

```bash
docker compose build
```

### 2) (Optional) Initialize or refresh the SQLite DB from CSV
```bash
docker compose --profile init run --rm loader
```

### 3) Start API

```bash
docker compose up api
```

The API will be available at `http://localhost:8000`

## Run Locally

From project root:
### 1) Install dependencies
If using uv:

```bash
uv sync
```
Or with pip:
```bash
pip install -r requirements.txt
```
### 2) (Optional) Load CSV into SQLite
```bash
python data/load_csv_to_db.py
```
### 3) Start the API
```bash
cd api
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```
## API Endpoints
### GET /bridge-data/
Query params:
- raw (bool, default false) – return raw DB rows if true
- freq (str, default 15min) – resampling frequency (5min, 15min, 1H, etc.)
- smooth_method (str, default ema) – ema or rolling
- span (int, default 5) – EMA span (used when smooth_method=ema)

Example:
```bash
curl "http://localhost:8000/bridge-data/?raw=false&freq=15min&smooth_method=ema&span=5"
```
### GET /debug/config (dev-only)
Enabled when `ENABLE_DEBUG_ENDPOINT=true.`

Returns resolved config paths and DB visibility checks.

## Testing

There is a test script that queries the data from the endpoint and then creates a visualisation.

### with UV (recommend)
```bash
uv run test_script.py
```

### As python file

Ensure that the venv has been activated:
```bash
source myenv/bin/activate # for Mac & Linux
source myenv\Scripts\activate # for windows
```

Then run the script:

```bash
python test_script.py
```

### Optional arguments
The script has optional arguments to adjust the end visualisation that relate to the arguments for the API call `GET /bridge-data/`:
- `--api`: change the address of the API endpoint if it differs from the default
- `--freq`: Change the resampling frequency (write this as a string, eg. `"10min"`)
- `--smooth`: Change between EMA and Rolling as the method for smoothing (EMA is better for this kind of data)
- `--span`: Changes the span used in EMA smoothing, this will do nothing if Rolling is the smoothing method
- `--overlay-raw`: Will query the endpoint twice to get the raw data so that it can be overlayed over the processed data

## Portfolio / Attribution Notice

This repository contains my independent implementation of a technical take-home assignment completed during a hiring process.

The code in this repository is my own work and is shared for portfolio/demo purposes only. 
No confidential company information, proprietary assets, or internal credentials are included.
This repository is not affiliated with or endorsed by the original company.

If any content is identified as confidential by the original requester, I will promptly remove or redact it.
