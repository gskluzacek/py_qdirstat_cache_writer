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
 Coming Soon...
 
## Future Enhancements
 Ability to scan multiple directories in parallel.
 
