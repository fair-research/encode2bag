import os
import os.path as osp
import sys
import logging
import shutil
import tempfile
import unittest
import json
import bagit
from bdbag import bdbag_api as bdb
from encode2bag import encode2bag_api as e2b
from encode2bag import get_named_exception as gne

if sys.version_info > (3,):
    from io import StringIO
else:
    from StringIO import StringIO

logging.basicConfig(filename='test_api.log', filemode='w', level=logging.DEBUG)
logger = logging.getLogger()


class TestAPI(unittest.TestCase):

    def setUp(self):
        super(TestAPI, self).setUp()
        self.stream = StringIO()
        self.handler = logging.StreamHandler(self.stream)
        logger.addHandler(self.handler)

        self.tmpdir = tempfile.mkdtemp(prefix="encode2bag_test_")

    def tearDown(self):
        if os.path.isdir(self.tmpdir):
            shutil.rmtree(self.tmpdir)
        self.stream.close()
        logger.removeHandler(self.handler)
        super(TestAPI, self).tearDown()

    def _testConvertMetadataToRemoteFileManifest(self, input_path, output_path, validation_path):
        try:
            e2b.convert_tsv_metadata_to_remote_file_manifest(input_path, output_path)
            self.assertTrue(osp.isfile(output_path))
            with open(output_path) as out_rmf:
                output_json = json.load(out_rmf)
                self.assertIsInstance(output_json, list, "Expected list of JSON objects")
                with open(validation_path) as in_rmf:
                    input_json = json.load(in_rmf)
                    self.assertEqual(input_json, output_json, "Expected JSON output to match test validation input")
        except Exception as e:
            self.fail(gne(e))

    def testConvertMetadataToRemoteFileManifest1(self):
        try:
            input_path = osp.abspath(osp.join("test", "test_data", "metadata-1.tsv"))
            output_path = osp.abspath(osp.join(self.tmpdir, "remote-file-manifest.json"))
            validation_path = osp.abspath(osp.join("test", "test_data", "rfm-1.json"))
            logger.info("testConvertMetadataToRemoteFileManifest1: input_path=%s output_path=%s validation_path=%s" %
                        (input_path, output_path, validation_path))
            self._testConvertMetadataToRemoteFileManifest(input_path, output_path, validation_path)
        except Exception as e:
            self.fail(gne(e))

    def testConvertMetadataToRemoteFileManifest2(self):
        try:
            input_path = osp.abspath(osp.join("test", "test_data", "metadata-2.tsv"))
            output_path = osp.abspath(osp.join(self.tmpdir, "remote-file-manifest.json"))
            validation_path = osp.abspath(osp.join("test", "test_data", "rfm-2.json"))
            logger.info("testConvertMetadataToRemoteFileManifest1: input_path=%s output_path=%s validation_path=%s" %
                        (input_path, output_path, validation_path))
            self._testConvertMetadataToRemoteFileManifest(input_path, output_path, validation_path)
        except Exception as e:
            self.fail(gne(e))

    def testRetrieveMetadataFileByURL1(self):
        try:
            url = "https://www.encodeproject.org/search/" \
                  "?type=Experiment&assay_title=RNA-seq&replicates.library.biosample.biosample_type=stem+cell"
            output_path = osp.abspath(self.tmpdir)
            logger.info("testRetrieveMetadataFileByURL1: url=%s output_path=%s" %
                        (url, output_path))
            self._testRetrieveMetadataFileByURL(url, output_path)
        except Exception as e:
            self.fail(gne(e))

    def testRetrieveMetadataFileByURL2(self):
        try:
            url = "https://www.encodeproject.org/batch_download/" \
                  "type=Experiment&assay_title=RNA-seq&replicates.library.biosample.biosample_type=stem+cell"
            output_path = osp.abspath(self.tmpdir)
            logger.info("testRetrieveMetadataFileByURL2: url=%s output_path=%s" %
                        (url, output_path))
            self._testRetrieveMetadataFileByURL(url, output_path)
        except Exception as e:
            self.fail(gne(e))

    def _testRetrieveMetadataFileByURL(self, url, output_path):
        metadata_file = e2b.retrieve_encode_metadata_file_by_url(url, output_path)
        self.assertTrue(osp.isfile(metadata_file))

    def testCreateBagFromMetadataFile1(self):
        try:
            metadata_file = osp.abspath(osp.join("test", "test_data", "metadata-1.tsv"))
            logger.info("testCreateBagFromMetadataFile1: metadata_file=%s" % metadata_file)
            bag_path = e2b.create_bag_from_metadata_file(metadata_file)
            self.assertTrue(osp.isdir(bag_path))
            self.assertIsInstance(bagit.Bag(bag_path), bagit.Bag)
            self.assertRaises(bagit.BagIncompleteError, bdb.validate_bag, bag_path, fast=True)
            shutil.rmtree(osp.abspath(osp.join(bag_path, os.pardir)))
        except Exception as e:
            self.fail(gne(e))

    def testCreateBagFromMetadataFile2(self):
        try:
            metadata_file = osp.abspath(osp.join("test", "test_data", "metadata-1.tsv"))
            output_name = "encode2bag_test_bag"
            logger.info("testCreateBagFromMetadataFile2: metadata_file=%s output_name=%s" %
                        (metadata_file, output_name))
            bag_path = e2b.create_bag_from_metadata_file(metadata_file,
                                                         output_name=output_name)
            self.assertTrue(osp.isdir(bag_path))
            self.assertIsInstance(bagit.Bag(bag_path), bagit.Bag)
            shutil.rmtree(osp.abspath(osp.join(bag_path, os.pardir)))
        except Exception as e:
            self.fail(gne(e))

    def testCreateBagFromMetadataFile3(self):
        try:
            metadata_file = osp.abspath(osp.join("test", "test_data", "metadata-2.tsv"))
            output_name = "encode2bag_test_bag"
            output_path = osp.join(self.tmpdir, "encode2bag_test")
            logger.info("testCreateBagFromMetadataFile3: "
                        "metadata_file=%s output_name=%s output_path=%s" %
                        (metadata_file, output_name, output_path))
            bag_path = e2b.create_bag_from_metadata_file(metadata_file,
                                                         output_path=output_path,
                                                         output_name=output_name)
            self.assertTrue(osp.isdir(bag_path))
            self.assertIsInstance(bagit.Bag(bag_path), bagit.Bag)
        except Exception as e:
            self.fail(gne(e))

    def testCreateBagFromMetadataFile4(self):
        try:
            metadata_file = osp.abspath(osp.join("test", "test_data", "metadata-1.tsv"))
            output_name = "encode2bag_test_bag"
            logger.info("testCreateBagFromMetadataFile4: metadata_file=%s output_name=%s" %
                        (metadata_file, output_name))
            bag_path = e2b.create_bag_from_metadata_file(metadata_file,
                                                         output_name=output_name,
                                                         archive_format="zip")
            self.assertTrue(osp.isfile(bag_path))
            shutil.rmtree(osp.abspath(osp.join(bag_path, os.pardir)))
        except Exception as e:
            self.fail(gne(e))

    def testCreateBagFromMetadataFile5(self):
        try:
            metadata_file = osp.abspath(osp.join("test", "test_data", "metadata-2.tsv"))
            output_name = "encode2bag_test_bag"
            output_path = osp.join(self.tmpdir, "encode2bag_test")
            logger.info("testCreateBagFromMetadataFile5: "
                        "metadata_file=%s output_name=%s output_path=%s" %
                        (metadata_file, output_name, output_path))
            bag_path = e2b.create_bag_from_metadata_file(metadata_file,
                                                         output_path=output_path,
                                                         output_name=output_name,
                                                         archive_format="tgz")
            self.assertTrue(osp.isfile(bag_path))
        except Exception as e:
            self.fail(gne(e))

    def testCreateBagFromMetadataFile6(self):
        try:
            metadata_file = osp.abspath(osp.join("test", "test_data", "metadata-2.tsv"))
            output_name = "encode2bag_test_bag"
            output_path = osp.join(self.tmpdir, "encode2bag_test")
            logger.info("testCreateBagFromMetadataFile6: "
                        "metadata_file=%s output_name=%s output_path=%s" %
                        (metadata_file, output_name, output_path))
            bag_path = e2b.create_bag_from_metadata_file(metadata_file,
                                                         output_path=output_path,
                                                         output_name=output_name,
                                                         creator_name="encode2bag unit test",
                                                         creator_orcid="0000-0003-2280-917X",
                                                         create_ro_manifest=True)
            self.assertTrue(osp.isdir(bag_path))
            self.assertIsInstance(bagit.Bag(bag_path), bagit.Bag)
            self.assertTrue(osp.isfile(osp.join(bag_path, "metadata", "manifest.json")))
        except Exception as e:
            self.fail(gne(e))

    def testCreateBagFromURL1(self):
        try:
            url = "https://www.encodeproject.org/batch_download/" \
                  "type=Experiment&assay_title=RNA-seq&replicates.library.biosample.biosample_type=stem+cell"
            output_name = "encode2bag_test_bag"
            output_path = osp.join(self.tmpdir, "encode2bag_test")
            logger.info("testCreateBagFromURL1: url=%s output_name=%s, output_path=%s" %
                        (url, output_name, output_path))
            bag_path = e2b.create_bag_from_url(url,
                                               output_name=output_name,
                                               output_path=output_path)
            self.assertTrue(osp.isdir(bag_path))
            self.assertIsInstance(bagit.Bag(bag_path), bagit.Bag)
        except Exception as e:
            self.fail(gne(e))

    def testCreateBagFromURL2(self):
        try:
            url = "https://www.encodeproject.org/search/" \
                  "?type=Experiment&assay_title=RNA-seq&replicates.library.biosample.biosample_type=stem+cell"
            output_name = "encode2bag_test_bag"
            output_path = osp.join(self.tmpdir, "encode2bag_test")
            logger.info("testCreateBagFromURL2: url=%s output_path=%s" %
                        (url, output_path))
            bag_path = e2b.create_bag_from_url(url,
                                               output_name=output_name,
                                               output_path=output_path)
            self.assertTrue(osp.isdir(bag_path))
            self.assertIsInstance(bagit.Bag(bag_path), bagit.Bag)
        except Exception as e:
            self.fail(gne(e))

    def testCreateBagFromURL3(self):
        try:
            url = "https://www.encodeproject.org/report/" \
                  "?type=Experiment&assay_title=RNA-seq&replicates.library.biosample.biosample_type=stem+cell"
            output_name = "encode2bag_test_bag"
            output_path = osp.join(self.tmpdir, "encode2bag_test")
            logger.info("testCreateBagFromURL3: url=%s output_name=%s, output_path=%s" %
                        (url, output_name, output_path))
            bag_path = e2b.create_bag_from_url(url,
                                               output_name=output_name,
                                               output_path=output_path)
            self.assertTrue(osp.isdir(bag_path))
            self.assertIsInstance(bagit.Bag(bag_path), bagit.Bag)
        except Exception as e:
            self.fail(gne(e))

    def testCreateBagFromURL4(self):
        try:
            url = "https://www.encodeproject.org/matrix/" \
                  "?type=Experiment&assay_title=RNA-seq&replicates.library.biosample.biosample_type=stem+cell"
            output_name = "encode2bag_test_bag"
            output_path = osp.join(self.tmpdir, "encode2bag_test")
            logger.info("testCreateBagFromURL4: url=%s output_name=%s, output_path=%s" %
                        (url, output_name, output_path))
            bag_path = e2b.create_bag_from_url(url,
                                               output_name=output_name,
                                               output_path=output_path)
            self.assertTrue(osp.isdir(bag_path))
            self.assertIsInstance(bagit.Bag(bag_path), bagit.Bag)
        except Exception as e:
            self.fail(gne(e))

    def testCreateBagFromURL5(self):
        try:
            url = "https://www.encodeproject.org/batch_download/" \
                  "type=Experiment&assay_title=RNA-seq&replicates.library.biosample.biosample_type=stem+cell"
            output_name = "encode2bag_test_bag"
            output_path = osp.join(self.tmpdir, "encode2bag_test")
            logger.info("testCreateBagFromURL5: url=%s output_name=%s, output_path=%s" %
                        (url, output_name, output_path))
            bag_path = e2b.create_bag_from_url(url,
                                               output_name=output_name,
                                               output_path=output_path,
                                               creator_name="encode2bag unit test",
                                               creator_orcid="0000-0003-2280-917X",
                                               create_ro_manifest=True)
            self.assertTrue(osp.isdir(bag_path))
            self.assertIsInstance(bagit.Bag(bag_path), bagit.Bag)
            self.assertTrue(osp.isfile(osp.join(bag_path, "metadata", "manifest.json")))
        except Exception as e:
            self.fail(gne(e))

    def testCreateBagFromURL6(self):
        try:
            url = "https://www.encodeproject.org/batch_download/" \
                  "type=Experiment&assay_title=RNA-seq&replicates.library.biosample.biosample_type=stem+cell"
            output_name = "encode2bag_test_bag"
            output_path = osp.join(self.tmpdir, "encode2bag_test")
            logger.info("testCreateBagFromURL6: url=%s output_name=%s, output_path=%s" %
                        (url, output_name, output_path))
            bag_path = e2b.create_bag_from_url(url,
                                               output_name=output_name,
                                               output_path=output_path,
                                               archive_format="tgz")
            self.assertTrue(osp.isfile(bag_path))
        except Exception as e:
            self.fail(gne(e))

    def testCreateBagFromURL7(self):
        try:
            url = "https://www.encodeproject.org/batch_download/" \
                  "type=Experiment&assay_title=RNA-seq&replicates.library.biosample.biosample_type=stem+cell"
            output_name = "encode2bag_test_bag"
            output_path = osp.join(self.tmpdir, "encode2bag_test")
            logger.info("testCreateBagFromURL7: url=%s output_name=%s, output_path=%s" %
                        (url, output_name, output_path))
            bag_path = e2b.create_bag_from_url(url,
                                               output_name=output_name,
                                               output_path=output_path,
                                               archive_format="zip")
            self.assertTrue(osp.isfile(bag_path))
        except Exception as e:
            self.fail(gne(e))

if __name__ == '__main__':
    unittest.main()
