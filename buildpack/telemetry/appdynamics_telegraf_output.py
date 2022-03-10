"""The module is used in runtime to convert metrics from telegraf for appdynamics Machine Agent"""
import json
import logging


METRIC_TREE_PATH = "MX App Runtime"
AGGR_TYPE = "AVERAGE"


def convert_payload():

    metrics_str = input()
    print(metrics_str)
    metrics_dict = json.loads(metrics_str)
    metrics_list = metrics_dict.get("metrics")

    if metrics_list is None:
        logging.error("Invalid format of metrics json (telegraf)")
        return

    appdynamics_payload = []

    for metric in metrics_list:

        appd_metric = {
            "metricName": "|".join((METRIC_TREE_PATH, metric["name"])),
            "aggregatorType": AGGR_TYPE,
            "value": int(metric["fields"]["value"])
        }

        appdynamics_payload.append(appd_metric)

    with open("/tmp/out.txt", "w") as f:

        f.write(f"Metric: {appdynamics_payload}")


if __name__ == "__main__":

    try:
        convert_payload()
    except Exception as e:
        with open("/tmp/err.txt", "w") as f:
            f.write(str(e))

#{"metrics":[{"fields":{"value": 0.016489,},"name":"process_cpu_usage","tags":{"app_name":"d5aa4abb-c2dc-4c9d-8a4d-f6c8e1e5a53d","host":"nonprod4denis-test.dev.mendixcloud.com-0","instance_index":"0","metric_type":"gauge","micrometer_metrics":true},"timestamp":1646922810}]}

# {"metrics":[{"fields":{"value": 0.016489},"name":"process_cpu_usage"}]}