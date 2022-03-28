import logging
import os
import subprocess
from distutils.util import strtobool
from buildpack import util

APPDYNAMICS_VERSION = "22.1.0.33445"
APPD_MACHINE_AGENT_VERSION = "22.2.0.3282"

AGENT_PATH = os.path.join(
    os.path.abspath(".local"), "machineagent", "bin", "machine-agent"
)

APPD_NODE_NUMBER = os.getenv("CF_INSTANCE_INDEX", default=0)
APPD_TIER = util.get_vcap_data()["application_name"]

APPD_DEFAULT_ENV_VARS = {
        "APPDYNAMICS_AGENT_APPLICATION_NAME": util.get_app_from_domain(),
        "APPDYNAMICS_AGENT_NODE_NAME": f"node_{APPD_NODE_NUMBER}",
        "APPDYNAMICS_AGENT_TIER_NAME": APPD_TIER,
        "APPDYNAMICS_CONTROLLER_PORT": "443",
        "APPDYNAMICS_CONTROLLER_SSL_ENABLED": "true",
    }


# def _actualize_default_env():

#    os_env_set = set(
#        os.environ
#    )

#    actual_env_vars = {}

#    for var_name, value in APPD_DEFAULT_ENV_VARS.items():

#        if not (var_name in os_env_set):
#            actual_env_vars[var_name] = value

#    return actual_env_vars


def _set_default_env(m2ee):
    for var_name, value in APPD_DEFAULT_ENV_VARS.items():
        util.upsert_custom_environment_variable(m2ee, var_name, value)


def stage(buildpack_dir, destination_path, cache_path):
    if appdynamics_used():
        util.resolve_dependency(
            util.get_blobstore_url(
                "/mx-buildpack/appdynamics/appdynamics-agent-1.8-{}.zip".format(
                    APPDYNAMICS_VERSION
                )
            ),
            destination_path,  # DOT_LOCAL_LOCATION,
            buildpack_dir=buildpack_dir,
            cache_dir=cache_path,  # CACHE_DIR,
        )

        if machine_agent_enabled():
            util.resolve_dependency(
                util.get_blobstore_url(
                    "/mx-buildpack/appdynamics/appdynamics-machineagent-bundle-{}.zip".format(
                        APPD_MACHINE_AGENT_VERSION
                    )
                ),
                destination_path + "/machineagent/",  # DOT_LOCAL_LOCATION,
                buildpack_dir=buildpack_dir,
                cache_dir=cache_path,  # CACHE_DIR,
            )


def update_config(m2ee, app_name):
    if not appdynamics_used():
        return
    logging.info("Adding app dynamics")
    _set_default_env(m2ee)
    util.upsert_javaopts(
        m2ee,
        [
            "-javaagent:{path}".format(
                path=os.path.abspath(
                    ".local/ver" + APPDYNAMICS_VERSION + "/javaagent.jar"
                )
            ),
            "-Dappagent.install.dir={path}".format(
                path=os.path.abspath(".local/ver" + APPDYNAMICS_VERSION)
            ),
        ],
    )

    APPDYNAMICS_AGENT_NODE_NAME = "APPDYNAMICS_AGENT_NODE_NAME"
    if os.getenv(APPDYNAMICS_AGENT_NODE_NAME):
        util.upsert_custom_environment_variable(
            m2ee,
            APPDYNAMICS_AGENT_NODE_NAME,
            "%s-%s"
            % (
                os.getenv(APPDYNAMICS_AGENT_NODE_NAME),
                os.getenv("CF_INSTANCE_INDEX", "0"),
            ),
        )


def run():
    if not machine_agent_enabled():
        return

    logging.info("Starting the appDynamics Machine agent...")
    env_dict = dict(os.environ)
    env_dict.update(APPD_DEFAULT_ENV_VARS)
    subprocess.Popen(
        (AGENT_PATH, "-Dmetric.http.listener=true"),
        env=env_dict,
    )

    logging.info(f"Machine Agent envs: {env_dict}")


def appdynamics_used():
    """
    The function checks if all required AppDynamics related
    environment variables are set.

    """

    required_envs = {
        "APPDYNAMICS_AGENT_ACCOUNT_ACCESS_KEY",
        "APPDYNAMICS_AGENT_ACCOUNT_NAME",
        "APPDYNAMICS_CONTROLLER_HOST_NAME"
    }

    os_env_set = set(
        os.environ
    )

    diff_envs = required_envs.difference(os_env_set)

    if len(diff_envs) == 0:
        logging.info("AppDynamics enabled.")
        return True

    else:
        logging.info(
            "AppDynamics disabled. Following required variables missed: {}".format(
                ",".join(diff_envs)
            )
        )

        return False


def machine_agent_enabled():

    if not appdynamics_used():
        return False

    is_machine_agent_enabled = strtobool(
        os.getenv(
            "APPDYNAMICS_MACHINE_AGENT_ENABLED", default="false"
        )
    )

    return is_machine_agent_enabled
