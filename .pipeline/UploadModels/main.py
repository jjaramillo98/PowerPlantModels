import json
import threading
import time
import sys

from jlog import Logger, Spinner
from azure.identity import DefaultAzureCredential
from azure.digitaltwins.core import DigitalTwinsClient
from azure.core.exceptions import HttpResponseError


class App:
    def __init__(self, dt_endpoint: str):
        self.spinner = Spinner.new(msg="In Progress")
        self.logger = Logger.get_instance("Pipeline")
        self.dt_client = DigitalTwinsClient(endpoint=dt_endpoint, credential=DefaultAzureCredential())

    @staticmethod
    def init(dt_endpoint: str):
        app = App(dt_endpoint)

        if len(sys.argv) == 2:
            app.logger.error("No input files. Exiting")
            exit()

        return app



def upload_models(dt_client: DigitalTwinsClient):
    logger.info("Finding Files.")
    file_paths = sys.argv[2:]
    models = []

    for file_path in file_paths:
        if file_path.endswith('.json'):
            file = open(file_path, 'r')
            models.append(json.load(file))
            file.close()
            logger.info("Found File %s", file_path)

    model_len = len(models)

    if model_len == 0:
        logger.warning("No Models to upload. Exiting.")
        exit()

    logger.info("Found %d valid models.", model_len)

    logger.info("Uploading Models")

    try:
        dt_client.create_models(models)
    except HttpResponseError as e:
        logger.error("Error when uploading models. Exiting")
        logger.exception(e)
        exit()

    logger.info("Finished Uploading Models")
    return models


def prev_version(model_id: str):
    model_version = model_id[model_id.rindex(";") + 1:]

    return model_id.replace(model_version, str(int(model_version) - 1))


def query_dt(dt_client: DigitalTwinsClient, model_id: str):
    prev_id = prev_version(model_id)

    query = f"SELECT * FROM DIGITALTWINS DT WHERE IS_OF_MODEL(DT, '{prev_id}')"

    paged_result = dt_client.query_twins(query_expression=query)

    for twin in paged_result:
        patch_document = [
            {
                "op": "replace",
                "path": "/$metadata/$model",
                "value": f"{model_id}"
            }
        ]

        dt_client.update_digital_twin(digital_twin_id=twin["$dtId"], json_patch=patch_document)


def update_twins(dt_client: DigitalTwinsClient, models: list):
    threads = list()

    for model in models:
        logger.info("Queing additional task to thread pool for model %d", model["@id"])
        thread = threading.Thread(target=query_dt, args=(dt_client, model["@id"], Logger.get_instance("UpdateTwins")))
        thread.start()
        threads.append(thread)

    return threads


def wait_for_completion(threads: list) -> bool:
    num_complete = 0

    for thread in threads:
        if not thread.isAlive():
            num_complete += 1

    return num_complete == len(threads)



def __run():
    start_time = time.time() * 1_000
    app = App.init(sys.argv[1])

    models = upload_models(app.dt_client, Logger.get_instance("UploadModels"))

    p_threads = update_twins(app.dt_client, models)

    logger.info("Waiting for completion")

    # TODO - Do better
    while not wait_for_completion(p_threads):
        _ = "Running"

    end_time = time.time() * 1_000

    logger.info("Updating Twins Complete in %d ms", round(end_time - start_time))


app = App.init(sys.argv[1])
logger = app.logger

__run()
