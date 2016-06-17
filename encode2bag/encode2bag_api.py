import sys
import os
import logging
import csv
import json
import requests
import shutil
import time
import datetime
import tempfile
import bdbag
from bdbag import bdbag_api as bdb
from collections import OrderedDict
import os.path as osp

if sys.version_info > (3,):
    from urllib.parse import urlsplit
else:
    from urlparse import urlsplit

logger = logging.getLogger(__name__)

ENCODE_FILE_URL = "File download URL"
ENCODE_FILE_SIZE = "Size"
ENCODE_FILE_MD5SUM = "md5sum"
REQUIRED_COLUMNS = {ENCODE_FILE_URL, ENCODE_FILE_SIZE, ENCODE_FILE_MD5SUM}
CHUNK_SIZE = 1024 * 1024


def configure_logging(level=logging.INFO, logpath=None):
    logging.captureWarnings(True)
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    if logpath:
        logging.basicConfig(filename=logpath, level=level, format=log_format)
    else:
        logging.basicConfig(level=level, format=log_format)


def get_target_bag_path(output_name=None, output_path=None):
    if output_name is None:
        output_name = ''.join(['encode_bag_', time.strftime("%Y-%m-%d_%H.%M.%S")])
    if output_path is not None:
        bag_path = osp.abspath(osp.join(output_path, output_name))
    else:
        bag_path = osp.abspath(osp.join(tempfile.mkdtemp(prefix="encode2bag_"), output_name))

    return bag_path


def ensure_bag_path_exists(bag_path, overwrite=False):

    if os.path.exists(bag_path):
        if overwrite:
            shutil.rmtree(bag_path)
        else:
            saved_bag_path = ''.join([bag_path, '_', time.strftime("%Y-%m-%d_%H.%M.%S")])
            logger.warn("Specified bag directory already exists -- moving it to %s" % saved_bag_path)
            shutil.move(bag_path, saved_bag_path)

    if not os.path.exists(bag_path):
        os.makedirs(bag_path)


def http_get_request_as_file(url, output_path):
    try:
        r = requests.get(url, stream=True)
        if r.status_code != 200:
            logger.error('HTTP GET Failed for url: %s' % url)
            logger.error("Host %s responded:\n\n%s" % (urlsplit(url).netloc,  r.text))
            raise RuntimeError('File [%s] transfer failed. ' % output_path)
        else:
            with open(output_path, 'wb') as data_file:
                for chunk in r.iter_content(CHUNK_SIZE):
                    data_file.write(chunk)
                data_file.flush()
            logger.info('File [%s] transfer successful.' % output_path)
    except requests.exceptions.RequestException as e:
        raise RuntimeError('HTTP Request Exception: %s %s' % (e.errno, e.message))


def retrieve_encode_metadata_file_by_url(url, output_path):
    url = url.replace("/search/?", "/batch_download/")
    logger.info("Attempting to get ENCODE batch download manifest from: %s" % url)
    manifest_file = osp.abspath(osp.join(output_path, "encode-manifest-file.txt"))
    http_get_request_as_file(url, manifest_file)

    metadata_url = None
    with open(manifest_file, 'r') as encode_manifest:
        for line in encode_manifest.readlines():
            metadata_url = line.strip("\r\n")
            break
    if not metadata_url:
        raise RuntimeError("Unable to locate metadata file URL in batch download file manifest %s" % output_path)
    metadata_file = osp.abspath(osp.join(output_path, metadata_url.split("/")[-1]))
    http_get_request_as_file(metadata_url, metadata_file)

    return metadata_file


def convert_tsv_metadata_to_remote_file_manifest(input_path, output_path):
    logger.info("Converting ENCODE metadata file to BDBag remote file manifest...")
    with open(input_path, "r") as metadata:
        reader = csv.DictReader(metadata, delimiter='\t')
        found = REQUIRED_COLUMNS.intersection(set(reader.fieldnames))
        if found != REQUIRED_COLUMNS:
            not_found = REQUIRED_COLUMNS - found
            raise RuntimeError("One or more required column names %s was not found in the column header %s" %
                               (not_found, str(reader.fieldnames)))
        with open(output_path, "w") as rfm:
            entries = list()
            for row in reader:
                entry = dict()
                url = row[ENCODE_FILE_URL]
                entry["url"] = url
                entry["length"] = row[ENCODE_FILE_SIZE]
                entry["filename"] = url.split("/")[-1]
                entry["md5"] = row[ENCODE_FILE_MD5SUM]
                entries.append(entry)
            json.dump(entries, rfm, sort_keys=True, indent=4)


def create_bag_from_metadata_file(metadata_file_path,
                                  remote_file_manifest=None,
                                  working_dir=None,
                                  output_name=None,
                                  output_path=None,
                                  archive_format=None):

    temp_path = None
    if remote_file_manifest is None:
        if working_dir is None:
            working_dir = temp_path = tempfile.mkdtemp(prefix="encode2bag_")
        remote_file_manifest = osp.abspath(osp.join(working_dir, "remote-file-manifest.json"))
    convert_tsv_metadata_to_remote_file_manifest(metadata_file_path, remote_file_manifest)

    bag_path = get_target_bag_path(output_name=output_name, output_path=output_path)
    ensure_bag_path_exists(bag_path)
    shutil.copy(osp.abspath(metadata_file_path), bag_path)

    bag = bdb.make_bag(bag_path, algs=['md5'], remote_file_manifest=remote_file_manifest)

    if archive_format:
        bag_path = bdb.archive_bag(bag_path, archive_format)

    if temp_path:
        shutil.rmtree(temp_path)

    return bag_path


def create_bag_from_url(url,
                        output_name=None,
                        output_path=None,
                        archive_format=None):

    temp_path = tempfile.mkdtemp(prefix="encode2bag_")
    metadata_file_path = retrieve_encode_metadata_file_by_url(url, temp_path)

    bag_path = create_bag_from_metadata_file(metadata_file_path,
                                             working_dir=temp_path,
                                             output_name=output_name,
                                             output_path=output_path,
                                             archive_format=archive_format)
    shutil.rmtree(temp_path)
    return bag_path


def register_minid_for_bag():
    pass

