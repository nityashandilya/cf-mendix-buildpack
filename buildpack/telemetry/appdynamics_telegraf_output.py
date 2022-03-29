"""The module is used in runtime to convert metrics from telegraf for appdynamics Machine Agent"""
import json
import logging
import requests
from requests.exceptions import ConnectionError


METRIC_TREE_BASE_NODE = "Custom Metrics|Mx Runtime Statistics"
AGGR_TYPE = "OBSERVATION"
MACHINE_AGENT_URL = "http://127.0.0.1:8293/api/v1/metrics"


def _filter_last(payload):
    """
    The function retrieves from the payload the latest version of
    each metric. It is required since the payload probably can
    contain buffered metrics. But Machine Agent HTTP listener payload
    doesn't support any timestamps.

    """

    last_metrics = {}

    for metric in payload:

        metric_name = metric["metricName"]
        last_metric = last_metrics.get(metric_name)

        if last_metric:
            if metric["timestamp"] > last_metric["timestamp"]:
                last_metrics[metric_name] = metric
        else:
            last_metrics[metric_name] = metric

    filtered_metrics = []

    for metric in last_metrics.values():
        del metric["timestamp"]
        filtered_metrics.append(metric)

    return filtered_metrics


def _convert_metric(metric):

    fields = metric.get("fields")

    converted = []

    if fields is None:
        logging.error("Invalid format of specific metric (telegraf)")
        return

    for value_name in fields.keys():
        value = fields[value_name]
        if value_name == "value":
            metric_name = metric["name"]
        else:
            metric_name = "_".join((metric["name"], value_name))

        metric_path_list = [METRIC_TREE_BASE_NODE, metric_name]

        tags = metric.get("tags")
        if tags:
            area = tags.get("area")
            id = tags.get("id")
            db = tags.get("db")

            if area:
                metric_path_list.append(area)
            if id:
                metric_path_list.append(id)
            if db:
                metric_path_list.append(db)

        metric_path = "|".join(metric_path_list)

        conv_metric = {
            "metricName": metric_path,
            "aggregatorType": AGGR_TYPE,
            "value": value,
            "timestamp": metric["timestamp"],
        }

        converted.append(conv_metric)

    return converted


def convert_and_push_payload():
    """
    The function collect metrics json from STDIN (Telegraf 'output.exec')
    and transform it to the structure of the compatible payload for the
    Machine Agent HTTP listener.
    AppDynamics Docs: https://docs.appdynamics.com/22.2/en/infrastructure-visibility/machine-agent/extensions-and-custom-metrics/machine-agent-http-listener

    """

    metrics_str = input()
    metrics_dict = json.loads(metrics_str)
    metrics_list = metrics_dict.get("metrics")

    if metrics_list is None:
        logging.error("Invalid format of metrics json (telegraf)")
        return

    appdynamics_payload = []

    for metric in metrics_list:
        # Convert each metric from Telegraf json structure
        # to the Machine Agent one.
        converted_metrics = _convert_metric(metric)

        if converted_metrics:
            appdynamics_payload.extend(converted_metrics)

    filtered_appd_payload = _filter_last(appdynamics_payload)

    try:
        resp = requests.post(MACHINE_AGENT_URL, json=filtered_appd_payload)
        logging.info(
            "Request to Machine Agent. Status code: {}".format(
                resp.status_code
            )
        )
    except ConnectionError as e:
        logging.error("Machine agent is unreachable. Error: {}".format(str(e)))


if __name__ == "__main__":

    convert_and_push_payload()
