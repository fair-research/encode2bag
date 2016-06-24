import argparse
import os
import sys
import logging
from encode2bag import encode2bag_api as e2b
from encode2bag import get_named_exception as gne


def parse_cli():
    description = 'Utility for converting ENCODE search URLs or metadata files into BDBags'

    parser = argparse.ArgumentParser(
        description=description, epilog="For more information see: http://github.com/ini-bdds/encode2bag")

    url_arg = parser.add_argument(
        '--url', metavar='<search url>',
        help="Optional path to an ENCODE search url e.g., \"https://www.encodeproject.org/search/?type="
             "Experiment&assay_title=RNA-seq&replicates.library.biosample.biosample_type=stem+cell\". "
             "Either this argument or the \"--metadata-file\" argument must be supplied.")

    metadata_file_arg = parser.add_argument(
        '--metadata-file', metavar='<file>',
        help="Optional path to a ENCODE format metadata file e.g., \"metadata.tsv\". "
             "Either this argument or the \"--url\" argument must be supplied.")

    parser.add_argument(
        '--output-name', metavar="<directory name>",
        help="Optional name for the output bag directory/bag archive file. "
             "If not specified, it will automatically be generated.")

    parser.add_argument(
        '--output-path', metavar="<path>",
        help="Optional path to a base directory in which the bag will be created. "
             "If not specified, a temporary directory will be created.")

    parser.add_argument(
        "--archiver", choices=['zip', 'tar', 'tgz'], help="Archive the output bag using the specified format.")

    parser.add_argument(
        '--create-ro-manifest', action="store_true",
        help="Generate a Research Object compatible manifest. See http://www.researchobject.org for more information.")

    parser.add_argument(
        '--creator-name', metavar="<person or entity name>",
        help="Optional name of the person or entity responsible for the creation of this bag, "
             "for inclusion in the bag metadata.")

    parser.add_argument(
        '--creator-orcid', metavar="<orcid>",
        help="Optional ORCID identifier of the bag creator, for inclusion in the bag metadata.")

    parser.add_argument(
        '--quiet', action="store_true", help="Suppress logging output.")

    parser.add_argument(
        '--debug', action="store_true", help="Enable debug logging output.")

    args = parser.parse_args()

    e2b.configure_logging(level=logging.ERROR if args.quiet else (logging.DEBUG if args.debug else logging.INFO))

    if not args.url and not args.metadata_file:
        sys.stderr.write("Error: Required argument missing: either the %s argument "
                         "or the %s argument must be specified.\n\n" %
                         (url_arg.option_strings, metadata_file_arg.option_strings))
        sys.exit(2)

    return args


def main():

    sys.stderr.write('\n')
    args = parse_cli()
    error = None
    result = 0

    try:
        if args.url:
            e2b.create_bag_from_url(args.url,
                                    output_name=args.output_name,
                                    output_path=args.output_path,
                                    archive_format=args.archiver,
                                    creator_name=args.creator_name,
                                    creator_orcid=args.creator_orcid,
                                    create_ro_manifest=args.create_ro_manifest)
        elif args.metadata_file:
            e2b.create_bag_from_metadata_file(args.metadata_file,
                                              output_name=args.output_name,
                                              output_path=args.output_path,
                                              archive_format=args.archiver,
                                              creator_name=args.creator_name,
                                              creator_orcid=args.creator_orcid,
                                              create_ro_manifest=args.create_ro_manifest)
    except Exception as e:
        result = 1
        error = "Error: %s" % gne(e)

    finally:
        if result != 0:
            sys.stderr.write("\n%s" % error)

    sys.stderr.write('\n')

    return result


if __name__ == '__main__':
    sys.exit(main())

