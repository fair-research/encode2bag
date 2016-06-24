import sys
import os
import logging
import copy
import csv
import json
import requests
import shutil
import time
import tempfile
from bdbag import bdbag_api as bdb
from bdbag import bdbag_ro as ro
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
    url = url.replace("/report/?", "/batch_download/")
    url = url.replace("/matrix/?", "/batch_download/")
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


def convert_tsv_metadata_to_remote_file_manifest(input_path, output_path, ro_manifest=None):
    logger.info("Converting ENCODE metadata file to BDBag remote file manifest...")
    file_list = list()
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
                filename = url.split("/")[-1]
                entry["url"] = url
                entry["length"] = row[ENCODE_FILE_SIZE]
                entry["filename"] = filename
                entry["md5"] = row[ENCODE_FILE_MD5SUM]
                entries.append(entry)
                if ro_manifest:
                    uri = ''.join(["../data/", filename])
                    file_list.append(uri)
                    ro.add_aggregate(ro_manifest, uri,
                                     mediatype=''.join(["application/x-", row["File format"]]),
                                     conforms_to=str("http://www.ebi.ac.uk/ols/search?q=%s&exact=on"
                                                     % row["Biosample term id"]))
            json.dump(entries, rfm, sort_keys=True, indent=4)
    if ro_manifest and len(file_list) > 0:
        ro.add_annotation(ro_manifest, file_list, content=''.join(["../data/", os.path.basename(input_path)]))


def create_bag_from_url(url,
                        output_name=None,
                        output_path=None,
                        archive_format=None,
                        creator_name=None,
                        creator_orcid=None,
                        create_ro_manifest=False):

    temp_path = tempfile.mkdtemp(prefix="encode2bag_")
    metadata_file_path = retrieve_encode_metadata_file_by_url(url, temp_path)

    bag_path = create_bag_from_metadata_file(metadata_file_path,
                                             working_dir=temp_path,
                                             output_name=output_name,
                                             output_path=output_path,
                                             archive_format=archive_format,
                                             creator_name=creator_name,
                                             creator_orcid=creator_orcid,
                                             create_ro_manifest=create_ro_manifest)
    shutil.rmtree(temp_path)
    return bag_path


def create_bag_from_metadata_file(metadata_file_path,
                                  remote_file_manifest=None,
                                  working_dir=None,
                                  output_name=None,
                                  output_path=None,
                                  archive_format=None,
                                  creator_name=None,
                                  creator_orcid=None,
                                  create_ro_manifest=False):

    temp_path = None
    if remote_file_manifest is None:
        if working_dir is None:
            working_dir = temp_path = tempfile.mkdtemp(prefix="encode2bag_")
        remote_file_manifest = osp.abspath(osp.join(working_dir, "remote-file-manifest.json"))

    ro_manifest = None
    if create_ro_manifest:
        ro_manifest = init_ro_manifest(creator_name=creator_name, creator_orcid=creator_orcid)

    convert_tsv_metadata_to_remote_file_manifest(metadata_file_path, remote_file_manifest, ro_manifest)

    bag_path = get_target_bag_path(output_name=output_name, output_path=output_path)
    ensure_bag_path_exists(bag_path)
    shutil.copy(osp.abspath(metadata_file_path), bag_path)

    bag_metadata = dict()
    if creator_name:
        bag_metadata["Contact-Name"] = creator_name
    if creator_orcid:
        bag_metadata["Contact-Orcid"] = creator_orcid

    bag = bdb.make_bag(bag_path,
                       algs=["md5", "sha256"],
                       metadata=bag_metadata,
                       remote_file_manifest=remote_file_manifest)

    if create_ro_manifest:
        bag_metadata_dir = os.path.abspath(os.path.join(bag_path, "metadata"))
        if not os.path.exists(bag_metadata_dir):
            os.mkdir(bag_metadata_dir)
        ro_manifest_path = osp.join(bag_metadata_dir, "manifest.json")
        ro.write_ro_manifest(ro_manifest, ro_manifest_path)
        bag_metadata.update({'BagIt-Profile-Identifier':
                            "http://raw.githubusercontent.com/ini-bdds/bdbag/master/profiles/bdbag-ro-profile.json"})
        bdb.make_bag(bag_path, update=True, metadata=bag_metadata)
    if archive_format:
        bag_path = bdb.archive_bag(bag_path, archive_format)

    if temp_path:
        shutil.rmtree(temp_path)

    return bag_path


def init_ro_manifest(creator_name=None, creator_uri=None, creator_orcid=None):
    manifest = copy.deepcopy(ro.DEFAULT_RO_MANIFEST)
    created_on = ro.make_created_on()
    created_by = None
    if creator_name:
        if creator_orcid and not creator_orcid.startswith("http"):
            creator_orcid = "/".join(["http://orcid.org", creator_orcid])
        created_by = ro.make_created_by(creator_name, uri=creator_uri, orcid=creator_orcid)
    ro.add_provenance(manifest, created_on=created_on, created_by=created_by)

    return manifest


def register_minid_for_bag():
    logger.error("Not implemented")

