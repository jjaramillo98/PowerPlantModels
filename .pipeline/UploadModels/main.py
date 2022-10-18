import json
import os
import sys
import time

from jlog import logger, Spinner
from azure.identity import DefaultAzureCredential
from azure.digitaltwins.core import DigitalTwinsClient

start_time = time.time() * 1_000
logger.info("Beginning Model Upload")

if len(sys.argv) == 1:
    logger.warning("No input files. Exiting")
    exit()

file_paths = sys.argv[1:]
models = []

logger.info("Finding Files.")

spinner = Spinner.new(msg="Parsing Models")

spinner.start()
for file_path in file_paths:
    if file_path.endswith('.json'):
        file = open(file_path, 'r')
        models.append(json.load(file))
        file.close()
        logger.info("Found File %s", file_path)
spinner.stop()

model_len = len(models)

if model_len == 0:
    logger.warning("No Models to upload. Exiting.")
    exit()

credential_provider = DefaultAzureCredential()
dt_host_endpoint = os.getenv("AZURE_URL")

dt_client = DigitalTwinsClient(
    endpoint=dt_host_endpoint,
    credential=credential_provider
)

# noinspection PyArgumentList
logger.info("Uploading %d models", model_len)

spinner = Spinner.new(msg="Uploading Models")
result = dt_client.create_models(models)
time.sleep(4)
spinner.stop()

logger.info("Finished Uploading Models")
