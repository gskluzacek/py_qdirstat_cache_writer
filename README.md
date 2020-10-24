# py_qdirstat_cache_writer
 Python (2.7) version of the qdirstat cache writer script
 See the original QDirStat GitHub repo here:
 https://github.com/shundhammer/qdirstat
 
## Motivation
 I wanted to run qdirstat_cache_writer on a Gluster volume so we could determine the people 
 who were abusing the file space by keeping large amounts of data. Because Gluster 
 keeps an internal index within the data volume being scanned, I needed a way to exclude this
 directory (.glusterfs) as the data is specific to the file system and not to a given user. 
 As the original qdirstat_cache_writer is writen in Perl, which I haven't used in 10 years 
 or more, I decied to port the program to python so that I could add the enhancements I
 wanted.
 
## Enhancements to the original
 As I mentioned above, the python version of qdirstat_cache_writer allows you to exclude various
 directories and files from being scaned. This is accomplished by passing the nane of a json
 config file as the only argument to qdirstat_cache_writer.py
 
 All of the original arguments can be specified in the json config file as well as the ability
 to specify multiple directories to be scanned (each with their own output cache file).
 
## JSON Config file specification

### Sample JSON Config file
 There are three top level configuration sections
 1. `options` - these are options that apply to the given execution as a whole
 2. `global_exclude` - this is a list of direcories or files that will be excluded for all root directories to be scanned
 3. `index_directories` - this is a list of root directories that will be scanned
```
{
  "options": {
    "long_format": false,
    "scan_mounted": false,
    "verbose": false,
    "debug": true
  },
  "global_exclude": [
    "tmp_tables",
    ".DS_Store"
  ],
  "index_directories": [
    {
      "index": "/data/us_markets/pen_sales_by_quarter",
      "cache": "/home/robert_nash/qdirstat_cache_1",
      "compress": false,
      "exclude": [
        "/data/us_markets/pen_sales_by_quarter/previous"
      ]
    }, {
      "index": "/data/emea_markets",
      "cache": "/home/robert_nash/qdirstat_cache_1",
      "compress": false,
      "exclude": [
        "/data/emea_markets/rework",
        "/data/emea_markets/errors",
      ]
    }

  ]
}
```

#### Options
 All of the original options of the Perl verions of qdirstat_cache_writer are supported
 in the json config file. 
 
	- `long_format` [-l]: **true** or **false** - always add full path, even for plain files
	- `scan_mounted` [-m]: **true** or **false**	- scan mounted ilesystems (cross filesystem boundaries)
	- `verbose` [-v]: **true** or **false**	- verbose output
 - `debug` [-d]: **true** or **false**	- debug ouput
 
 Note: if `debug` is set to **true** then verbose will also be **true**
 
 The options speacified here will apply to the given execution of the program as a whole. That is 
 they will apply to each directory specified in the `index_directory` section.

#### Excluding Directories & Files
 You can specify a list of zero or more files or directories that will not be scanned and thus excluded 
 from each of the output cache files that are generated. The paths specified can either be absolute 
 (starting with a `/`) or relative.
 
 The list of Globally Excluded paths will be merged with the Excluded paths for each Index Directory
 that is configured.
 
 Currently only simple matching has been implemented. A give path being scanned must either be an exact 
 match to one of the absolute paths specified or must end with one of the relative paths specified. Wild
 cards (`*` and `?`) and regular expressions are not supported at this time.
 
 For example, if the following paths have been specified as excluded:
 - `"/bin"`
 - `"tmp"`
 - `".hidden"`
 - `".csv"`
 
 Then each of the following directories/files would be excluded/not-excluded
 - `/bin` from the root diretory would be excluded
 - `/home/msmith/bin` would **not be** excluded
 - `/tmp` from the root diretory would be excluded
 - `/home/msmith/tmp` would be excluded
 - `/usr/local/data_tmp` would be excluded
 - `/usr/local/tmp_copy` would  **not be** excluded
 - `.hidden` would be excluded
 - `/home/msmith/.hidden` would be excluded
 - `/home/msmith/data.hidden` would be excluded
 - `/home/msmith/quarter_1_2020.csv` would be excluded
 
#### Global Excludes
 Any directory or file specified in the `global_excludes` configuration list will be excluded from 
 the output cache files that are generated for each configured Index Directory. Either absolute or
 relative paths can be specified, but it makes more sense to specify relative paths as they will be
 applied to each configured Index Directory.

#### Index Directories
 In the `index_directory` configuratin section, you can configure 1 or more directories to be scanned.
 Each sub-section must contain the following.
 1. `index` - the directory path to be scanned
 2. `cache` - the file path to write the generated cache file to.
 3. `compress` - **true** or **false**: if set to true the cache file will be compressed
 4. `exclude` - a list of zeror or more absolute or relative directories or files not to scan
 
 Note: the compress configuration has not yet been implimented.
 
## Future Enhancements
 - Ability to scan multiple directories in parallel.
 - file/diretory globbing for exclusions
 - support for compressing the output cache files
