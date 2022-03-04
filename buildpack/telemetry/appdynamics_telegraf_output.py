"""The module is used in runtime to convert metrics from telegraf for appdynamics Machine Agent"""
import json
import logging
import requests
from requests.exceptions import ConnectionError


METRIC_TREE_BASE_NODE = "Custom Metrics|Mx Runtime Statistics"
AGGR_TYPE = "OBSERVATION"
MACHINE_AGENT_URL = "http://127.0.0.1:8293/api/v1/metrics"


def filter_last(payload):

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


def convert_metric(metric):

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


def convert_payload():

    metrics_str = input()
    metrics_dict = json.loads(metrics_str)
    metrics_list = metrics_dict.get("metrics")

    with open("/tmp/test.json", "w") as f:
        json.dump(metrics_dict, f, indent=4)

    if metrics_list is None:
        logging.error("Invalid format of metrics json (telegraf)")
        return

    appdynamics_payload = []

    for metric in metrics_list:

        converted_metrics = convert_metric(metric)

        if converted_metrics:
            appdynamics_payload.extend(converted_metrics)

    filtered_appd_payload = filter_last(appdynamics_payload)

    with open("/tmp/conv.json", "w") as f:
        f.write(str(filtered_appd_payload))

    try:
        resp = requests.post(MACHINE_AGENT_URL, json=filtered_appd_payload)
        with open("/tmp/resp.txt", "w") as f:
            f.write(str(resp.status_code))
    except ConnectionError as e:
        logging.error("Machine agent is unreachable.")
        with open("/tmp/err.txt", "w") as f:
            f.write(str(e))


if __name__ == "__main__":

    try:
        convert_payload()
    except Exception as e:
        with open("/tmp/err2.txt", "w") as f:
            f.write(str(e))
