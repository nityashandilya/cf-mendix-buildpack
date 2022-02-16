import logging
import os
import subprocess
import shutil

from buildpack import util


def stage(buildpack_dir, destination_path, cache_path):

    logging.info("Stage opentelemetry")
    util.resolve_dependency(
        util.get_blobstore_url("/opentelemetry/opentelemetry-javaagent.jar"),
        destination_path,  # DOT_LOCAL_LOCATION,
        unpack=False,
        buildpack_dir=buildpack_dir,
        cache_dir=cache_path,  # CACHE_DIR,
    )

    logging.info("Stage opentelemetry collector")
    util.resolve_dependency(
        util.get_blobstore_url(
            "/opentelemetry/otelcol-contrib_0.44.0_linux_amd64.tar.gz"
        ),
        destination_path,  # DOT_LOCAL_LOCATION,
        unpack=True,
        buildpack_dir=buildpack_dir,
        cache_dir=cache_path,  # CACHE_DIR,
    )

    shutil.copy(
        os.path.join(
            buildpack_dir,
            "etc",
            "opentelemetry",
            "otel.yml",
        ),
        os.path.join(
            destination_path,
            "otel.yml",
        ),
    )


def update_config(m2ee, app_name):

    logging.info("Adding opentelemetry javaagent")
    logging.info(app_name)
    util.upsert_javaopts(
        m2ee,
        [
            "-javaagent:{path}".format(
                path=os.path.abspath(".local/opentelemetry-javaagent.jar")
            ),
        ],
    )


def run():

    logging.info("Starting the opentelemetry collector...")
    e = dict(os.environ)

    subprocess.Popen(
        (".local/otelcol-contrib", "--config", ".local/otel.yml"),
        env=e,
    )
