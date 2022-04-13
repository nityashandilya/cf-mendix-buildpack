import logging
import os

from buildpack import util


NAMESPACE = "fluentbit"
FLUENTBIT_VERSION = "1.9.1"
FLUENTBIT_ARCHIVE_NAME = "fluent-bit-{}.tar.gz".format(FLUENTBIT_VERSION)


def stage(buildpack_dir, destination_path, cache_path):

    logging.info("Staging Fluent Bit log processor...")

    fluentbit_cdn_path = os.path.join(
        "/mx-buildpack", NAMESPACE, FLUENTBIT_ARCHIVE_NAME
    )

    util.resolve_dependency(
        util.get_blobstore_url(fluentbit_cdn_path),
        # destination_path - DOT_LOCAL_LOCATION
        os.path.join(destination_path, NAMESPACE),
        buildpack_dir=buildpack_dir,
        cache_dir=cache_path,
    )
