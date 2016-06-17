# encode2bag
[![Build Status](https://travis-ci.org/ini-bdds/encode2bag.svg)](https://travis-ci.org/ini-bdds/encode2bag)

Utility for converting ENCODE search URLs or metadata files into BDBags

### Dependencies

* [Python 2.7](https://www.python.org/downloads/release/python-2711/) is the minimum Python version required.
* The code and dependencies are currently compatible with Python 3.


### Installation
Download the current [encode2bag](https://github.com/ini-bdds/encode2bag/archive/master.zip) source code from GitHub or
alternatively clone the source from GitHub if you have *git* installed:

```sh
git clone https://github.com/ini-bdds/encode2bag
```
From the root of the **encode2bag** source code directory execute the following command:
```sh
python setup.py install --user
```

Note that if you want to make **encode2bag** available to all users on the system, you should run the following command:
```sh
python setup.py install
```
If you are on a Unix-based system (including MacOS) you should execute the above command as **root** or use **sudo**.

### Testing
The unit tests can be run by invoking the following command from the root of the **encode2bag** source code directory:
```sh
python setup.py test
```

### Usage:

```
usage: encode2bag_cli.py [-h] [--url <search url>] [--metadata-file <file>]
                         [--output-name <directory name>]
                         [--output-path <path>] [--archiver {zip,tar,tgz}]
                         [--quiet] [--debug]

Utility for converting ENCODE search URLs or metadata files into BDBags

optional arguments:
  -h, --help            show this help message and exit
  --url <search url>    Optional path to an ENCODE search url e.g., "https://w
                        ww.encodeproject.org/search/?type=Experiment&assay_tit
                        le=RNA-seq&replicates.library.biosample.biosample_type
                        =stem+cell". Either this argument or the "--metadata-
                        file" argument must be supplied.
  --metadata-file <file>
                        Optional path to a ENCODE format metadata file e.g.,
                        "metadata.tsv". Either this argument or the "--url"
                        argument must be supplied.
  --output-name <directory name>
                        Optional name for the output bag directory/bag archive
                        file. If not specified, it will automatically be
                        generated.
  --output-path <path>  Optional path to a base directory in which the bag
                        will be created. If not specified, a temporary
                        directory will be created.
  --archiver {zip,tar,tgz}
                        Archive the output bag using the specified format.
  --quiet               Suppress logging output.
  --debug               Enable debug logging output.
```