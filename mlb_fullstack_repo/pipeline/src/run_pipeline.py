import json
import requests
from .config import SUPABASE_INGEST_URL, PIPELINE_INGEST_SECRET, validate_runtime_env
from .sample_data import make_sample_payload


def main():
    validate_runtime_env()

    payload = make_sample_payload()
    response = requests.post(
        SUPABASE_INGEST_URL,
        headers={"content-type": "application/json", "x-pipeline-secret": PIPELINE_INGEST_SECRET},
        data=json.dumps(payload),
        timeout=60,
    )
    print("Status:", response.status_code)
    print(response.text)
    response.raise_for_status()


if __name__ == "__main__":
    main()
