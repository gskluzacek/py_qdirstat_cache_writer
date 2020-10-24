"""
    to be fully compatible the following command line format and options need to be implemented

        $0 [-ldvh] <directory> [<cache-file-name>]

        If not specified, <cache-file-name> defaults to \"$default_cache_file_name\"
        in <directory>.

        If <cache-file-name> ends with \".gz\", it will be compressed with gzip.
        qdirstat can read gzipped and plain text cache files.

        -l	long format - always add full path, even for plain files
        -m	scan mounted filesystems (cross filesystem boundaries)
        -v	verbose
        -d	debug
        -h	help (this usage message)

    I would like to add an option to exclude certain directories either passed in or in a .ignore file
    or something like that

        -e <exclude-dir-1> <exclude-dir-2> ...
"""
import os
import sys
import stat
import urllib
import time
import logging
import argparse
import json

logging.basicConfig(format='[%(asctime)s] %(levelname)s: %(message)s')


class DirStatError(Exception):
    pass


class DirItem:
    def __init__(self, path, name=None):
        if not name:
            path, name = os.path.split(path)
        self.name = name
        self.path = os.path.join(path, name)
        self.o_path = self.path
        self.name = self.name.encode("utf8")
        self.path = self.path.encode("utf8")
        self.lstats = None
        try:
            self.lstats = os.lstat(self.o_path)
        except OSError as e:
            logging.warning('lstat() failed for %s: %s', self.path, str(e))

    @property
    def exists(self):
        return True if self.lstats else False

    @property
    def safe_path(self):
        try:
            return urllib.quote(self.path.replace('//', '/'))
        except KeyError as e:
            logging.error('could not get safe path for: {} ## {}'.format(self.path, str(e)))

    @property
    def safe_name(self):
        try:
            return urllib.quote(self.name)
        except KeyError as e:
            logging.error('could not get safe name for: {} ## {}'.format(self.path, str(e)))

    @property
    def dev_nbr(self):
        return self.lstats.st_dev

    @property
    def size(self):
        return self.lstats.st_size

    @property
    def mtime(self):
        return self.lstats.st_mtime

    @property
    def mode(self):
        return self.lstats.st_mode

    @property
    def blocks(self):
        return self.lstats.st_blocks

    @property
    def links(self):
        return self.lstats.st_nlink

    @property
    def is_dir(self):
        return stat.S_ISDIR(self.mode)

    @property
    def type(self):
        f_type = 'F'
        if stat.S_ISREG(self.mode):
            f_type = 'F'
        elif stat.S_ISLNK(self.mode):
            f_type = 'L'
        elif stat.S_ISBLK(self.mode):
            f_type = 'BlockDev'
        elif stat.S_ISCHR(self.mode):
            f_type = 'CharDev'
        elif stat.S_ISFIFO(self.mode):
            f_type = 'FIFO'
        elif stat.S_ISSOCK(self.mode):
            f_type = 'Socket'
        return f_type

    def list_dir(self):
        try:
            return os.listdir(self.o_path)
        except OSError as e:
            logging.warning("Can't open directory %s: %s", self.path, str(e))
            return None


class DirStat:
    def __init__(
            self, top_lvl_dir, cache_file_name, scan_mounted=False, long_format=False,
            compress_opt=False, exclude_dirs=None
    ):
        self.dir_itm = DirItem(top_lvl_dir)
        self.cache_file_name = cache_file_name
        self.cache_file = None
        self.scan_mounted = scan_mounted
        self.long_format = long_format
        self.compress_opt = compress_opt
        self.exclude_dirs = exclude_dirs or []
        self.def_dev_name, self.dev_name_lkup = self.get_device_names()
        self.dev_name = self.device_name(self.dir_itm)

    @staticmethod
    def get_device_names():
        dev_name_lkup = {}
        def_dev_name = None
        df_output_lines = [s.split() for s in os.popen("df -Ph").read().splitlines()][1:]
        for line in df_output_lines:
            if line[-1] != '/':
                dev_name_lkup[line[-1]] = line[0]
            else:
                def_dev_name = line[0]
        if not def_dev_name:
            raise DirStatError('device name for root mount point not found, check output for `df -Ph`')
        return def_dev_name, dev_name_lkup

    def device_name(self, dir_item):
        dev_name = [self.dev_name_lkup[mount] for mount in self.dev_name_lkup.keys() if dir_item.path.startswith(mount)]
        if not dev_name:
            dev_name = self.def_dev_name
        logging.debug('Directory %s is on device %s', dir_item.path, dev_name)
        return dev_name

    def write_cache_file(self):
        start_time = time.time()
        with open(self.cache_file_name, 'wb') as self.cache_file:
            # TODO: original perl code calls the following, not sure what it does: binmode( CACHE, ":bytes" );
            self.write_cache_header()
            self.write_cache_tree(self.dir_itm, first_flag=True)

            elapsed = time.gmtime(time.time() - start_time)
            tm_hour, tm_min, tm_sec = (elapsed.tm_hour, elapsed.tm_min, elapsed.tm_sec)
            # output as: "# Elapsed time: %d:%02d:%02d\n", $hours, $min, $sec;
            self.cache_file.write('# Elapsed time: {}:{:02d}:{:02d}\n'.format(tm_hour, tm_min, tm_sec))

    def write_cache_header(self):
        # TODO: compare number of blank lines between header and beginning of output
        header = """\
[qdirstat 1.0 cache file]
# Generated by qdirstat-cache-writer
# Do not edit!
#
# Type  path            size    mtime           <optional fields>


"""
        self.cache_file.write(header)

    def write_cache_tree(self, curr_dir_item, first_flag=False):
        dir_list = []
        file_list = []

        logging.info('Reading %s', curr_dir_item.path)
        if not self.write_dir_entry(curr_dir_item, first_flag):
            return

        dir_listing = curr_dir_item.list_dir()
        if dir_listing is None:
            self.cache_file.write("# Can't open {}: OSError\n".format(curr_dir_item.path))
        dir_listing.sort()

        for item in dir_listing:
            dir_item = DirItem(curr_dir_item.path, item)
            if not dir_item.lstats:
                logging.warning('lstat() for %s: OSError', os.path.join(curr_dir_item.path, item))
                continue
            if (
                dir_item.path in self.exclude_dirs or
                any([dir_item.path.endswith(excld) for excld in self.exclude_dirs])
            ):
                logging.info('skipping excluded directory %s', dir_item.path)
                continue
            if dir_item.is_dir:
                dir_list.append(dir_item)
            else:
                file_list.append(dir_item)

        for f_dir_item in file_list:
            self.write_file_entry(f_dir_item)

        for d_dir_item in dir_list:
            self.write_cache_tree(d_dir_item)

    def write_dir_entry(self, dir_item, first_flag=False):
        self.cache_file.write('D {}\t{}\t0x{:x}\n'.format(dir_item.safe_path, dir_item.size, int(dir_item.mtime)))
        if first_flag:
            self.cache_file.write('# Device: {}\n\n'.format(self.dev_name))
        if dir_item.dev_nbr == self.dir_itm.dev_nbr or self.scan_mounted:
            return True

        dev_name = self.device_name(dir_item)
        fs_boundary = dev_name != self.dev_name

        if fs_boundary:
            msg = 'Filesystem boundary at mount point {} on device {}'.format(dir_item.path, dev_name)
        else:
            msg = 'Mount point {} is still on the same device {}'.format(dir_item.path, dev_name)

        self.cache_file.write('# {}\n\n'.format(msg))
        logging.info('%s', msg)

        return fs_boundary

    def write_file_entry(self, dir_item):
        self.cache_file.write('{}{}\t{}\t0x{:x}{}{}\n'.format(
            dir_item.type,
            ' ' + dir_item.safe_path if self.long_format else '\t' + dir_item.safe_name,
            dir_item.size,
            int(dir_item.mtime),
            '\t' + str(dir_item.blocks) if dir_item.blocks > 0 and dir_item.blocks * 512 < dir_item.size else '',
            '\t' + str(dir_item.links) if dir_item.links > 0 else ''
        ))

    def compress_file(self):
        logging.info('Compressing %s', self.cache_file_name)
        # TODO: implement file compression logic


def get_absolute_path(path):
    # TODO: write this code to take any path and make it an absolute path
    return path


def parse_arguments():
    index_dirs = []
    if len(sys.argv) == 2 and sys.argv[1].endswith('.json'):
        debug, verbose = args_from_json_config(index_dirs)
    else:
        debug, verbose = parse_cmd_line_args(index_dirs)

    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif verbose:
        logging.getLogger().setLevel(logging.INFO)

    return index_dirs


def parse_cmd_line_args(index_dirs):
    # else use argparse and only get options from command line
    # 1 or 2 positional arguments are required
    # ARG #1 - the program needs to get the top level directory to scan from the 1st positional argument
    # ARG #2 - the program needs to get the name of the output file from the 2nd positional argument if present
    # if ARG #2 is not present, default to ".qdirstat.cache.gz"

    # todo: parse input arguments !!!

    long_format = False
    scan_mounted = False
    verbose = False
    debug = False

    toplevel_dir = '/opt/cylance'
    cache_file_name = '/home/centos/greg/pytest.txt'

    exclude_dirs = []
    # TODO: derive compress option from filename extension
    compress_opt = False

    toplevel_dir = get_absolute_path(toplevel_dir)

    dir_stat = DirStat(toplevel_dir, cache_file_name, scan_mounted, long_format, compress_opt, exclude_dirs)
    index_dirs.append(dir_stat)

    return debug, verbose


def args_from_json_config(index_dirs):
    # if there is only 1 argument and it ends with .json
    #   treat it as an input configuration file and don't
    #   use argparse. Instead read ALL options from the json file.
    print "reading configuration..."

    config_file = sys.argv[1]
    try:
        json_file = open(config_file)
        config = json.load(json_file)
    except IOError as e:
        print "ERROR: could not open json config file: {}".format(config_file)
        print "\t{}".format(str(e))
        sys.exit(1)
    except ValueError as e:
        print "ERROR: could not parse json config file: {}".format(config_file)
        print "\t{}".format(str(e))
        sys.exit(2)
    except Exception as e:
        print "ERROR: an unexpected error occurred while processing json config file: {}".format(config_file)
        print "\t{}".format(str(e))
        sys.exit(-1)

    options = config.get('options')
    if not options:
        long_format = False
        scan_mounted = False
        verbose = False
        debug = False
    else:
        long_format = options.get('long_format', False)
        scan_mounted = options.get('scan_mounted', False)
        verbose = options.get('verbose', False)
        debug = options.get('debug', False)

    global_exclude = config.get('global_exclude', [])

    index_directories = config.get('index_directories', [])
    if not index_directories:
        print 'ERROR: Missing `index_directories`, please check json config file: {}'.format(config_file)
        sys.exit(3)

    for i, idx_dir in enumerate(index_directories, 1):
        top_lvl_dir = idx_dir.get('index')
        if not top_lvl_dir:
            print 'ERROR: missing `index` top level directory config for directory config item {} ' \
                  '-- skipping'.format(i)
            continue
        top_lvl_dir = get_absolute_path(top_lvl_dir)

        cache_file_name = idx_dir.get('cache')
        if not cache_file_name:
            print 'ERROR: missing `cache` cache file name config for directory config item {} ' \
                  '-- skipping'.format(i)
            continue

        compress_opt = idx_dir.get('compress', False)

        exclude_dirs = set(idx_dir.get('exclude', []))
        exclude_dirs.update(global_exclude)
        exclude_dirs = [excld.encode("utf8") for excld in exclude_dirs]

        dir_stat = DirStat(top_lvl_dir, cache_file_name, scan_mounted, long_format, compress_opt, exclude_dirs)
        if not dir_stat.dir_itm.exists or not dir_stat.dir_itm.is_dir:
            print 'The given path either does not exist or is not a directory: {} ' \
                  '-- skipping'.format(dir_stat.dir_itm.path)
            continue
        index_dirs.append(dir_stat)

    if not index_dirs:
        print 'No valid `index_directories` were specified, please check json config file: {}'.format(config_file)
        sys.exit(4)

    return debug, verbose


def main():
    index_dirs = parse_arguments()

    # todo: change logic so that if the current dir_stat fails, it is skipped instead of the whole execution failing
    try:
        for dir_stat in index_dirs:
            dir_stat.write_cache_file()
            dir_stat.compress_file()
    finally:
        print "exiting..."


if __name__ == '__main__':
    main()
