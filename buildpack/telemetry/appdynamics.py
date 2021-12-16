import logging
import os
import subprocess

from buildpack import util

APPDYNAMICS_VERSION = "21.11.1.33280"


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

        # Remove the JndiLookup class from classpath to mitigate CVE-2021-45046
        cmd = [
            "zip",
            "-d",
            os.path.abspath(destination_path + "/ver" + APPDYNAMICS_VERSION + "/lib/tp/log4j-core-*.jar"),
            "org/apache/logging/log4j/core/lookup/JndiLookup.class"
        ]
        logging.info("Executing %s" % str(cmd))
        subprocess.check_call(cmd)

def update_config(m2ee, app_name):
    if not appdynamics_used():
        return
    logging.info("Adding app dynamics")

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

def appdynamics_used():
    for key, _ in os.environ.items():
        if key.startswith("APPDYNAMICS_"):
            return True
    return False
