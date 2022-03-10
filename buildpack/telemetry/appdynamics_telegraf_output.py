"""The module is used in runtime to convert metrics from telegraf for appdynamics Machine Agent"""


def convert_payload():

    metric_str = input()

    with open("/tmp/out.txt", "w") as f:

        f.write(f"Metric: {metric_str}")


if __name__ == "__main__":

    convert_payload()
