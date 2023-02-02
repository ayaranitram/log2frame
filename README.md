# `log2frame`

`import log2frame`

A function to read well log data in LAS, LIS and DLIS formats and extract curves data as DataFrame.

The curves and header data are stored in an instance of `Log` class, designed to hold this data and operate with it.
If multiple log files are read together, the __Log__ instances are packed in a `Pack` instance, designed to hold `Log` instances and operate with them.

# to read log files
Simply call the function `read()` with the path or path pattern as argument:

## a single log file
To load a single _.las_, _.lis_ or _.dlis_ file. The function will return a `Log` instance containing the data:  
- `log2frame.read( path_to_file )` 

## several files in a folder  
To load several files at once. In this case the `read()` function will return a `Pack` instance containing a `Log` instance for each log file:  
- `log2frame.read( path_to_folder_containing_files/*.* )` 
By default, any invalid file will be ignored, thus, there is no problem to have other files in the same folder as the log files.

## several files recursively
To read files recursively in subdirectories, use the appropriate `fnmatch` pattern:  
- `log2frame.read( path_to_folder_containing_files/*/*.* )`

# further examples and details
Please refer to the Jupyter notebook <a href="https://github.com/ayaranitram/log2frame/blob/master/log2frame_demo.ipynb">**log2frame_demo**</a> for further examples and details on how to use **`log2frame`**.  
The sample data is publicly available at <a href="https://www.nlog.nl/en">**NLOG**</a>.
