# Irmos Technical task

This is the README detailing how to set up, run, and test the take-home task.

## Setup Instructions

1. **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/irmos-technical-task.git
    cd irmos-technical-task
    ```

2. **Build and run with Docker:**
    ```bash
    docker build -t irmos-task .
    docker run -p 8000:8000 irmos-task
    ```

    This will start the application on port 8000.

## Running Locally (without Docker)

1. **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

2. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3. **Run the application:**
    ```bash
    python main.py
    ```

## Testing

To run the tests, use:
```bash
pytest
```
or, if using Docker:
```bash
docker run irmos-task pytest
```

## Project Structure

- `main.py` - Entry point for the application.
- `app/` - Application source code.
- `tests/` - Test suite.
- `requirements.txt` - Python dependencies.
- `Dockerfile` - Docker build instructions.

## Notes

- Ensure Docker is installed if using the Docker workflow.
- The API will be available at `http://localhost:8000/` after starting the service.
- For any issues, please open an issue in the repository.