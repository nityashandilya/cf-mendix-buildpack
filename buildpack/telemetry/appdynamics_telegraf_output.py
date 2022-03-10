"""The module is used in runtime to convert metrics from telegraf for appdynamics Machine Agent"""


def convert_payload():

    metric_str = input()

    print("Metric: ", metric_str)


if __name__ == "__main__":

    convert_payload()
