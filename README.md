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
    "do_not_enter",
    ".DS_Store"
  ],
  "index_directories": [
    {
      "index": "/Users/gskluzacek/test_qdirstat",
      "cache": "/Users/gskluzacek/qdirstat_cache_2.txt",
      "compress": false,
      "exclude": [
        "/Users/gskluzacek/test_qdirstat/full_path_dont_index"
      ]
    }
  ]
}
```

#### Options
 coming soon

#### Global Excludes
 coming soon

#### Index Directories
 coming soon
 
## Future Enhancements
 - Ability to scan multiple directories in parallel.
 - file/diretory globbing for exclusions
 
