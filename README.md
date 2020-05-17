# What is the Google Forms Response Parser (FRP)?
In using Google Forms for any sort of data collection, oftentimes the native data analyzer provided by Google, adn the excel files that come with it, are not sufficient for analyzing data, especially for combining and viewing/analyzing data from multiple variable perspectives at once. 

FRP attempts to make analyzing data easier by taking in either the Google-Form output excel sheet or a native Form-editing web link (coming soon!) and graphing that data in easy-to-configure ways using python's matplotlib. 

Because the data retrieved by Google Forms is generally one user per response, the most common use case is to graph data by analyzing the number of people who responded in a certain way. Thus, the only type of graph that FRP currently offers is the bar graph.

You can use FRP to filter and graph data in many ways, and this tutorial will show you everything FRP has to offer. 

# How to use FRP

To run FRP, simply download the parser.py file located in this repository. FRP has no Python2 compatibility, and is best when run with Python 3.7. 

FRP's dependencies are: 
	- matplotlib
	- numpy
	- requests (currently not yet a dependency, but coming soon)

FRP has only one required input: a json-format file that serves as the configuration for how FRP should parse and analyze data. 

To run FRP, simply use `python3 parser.py [json filename]`. 

FRP currently only supports input excel files of type .xls, rather than the newer standard .xlsx. However, note that any .xlsx can be converted to .xls using Microsoft Excel. 
