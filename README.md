# What is the Google Forms Response Parser (FRP)?
In using Google Forms for any sort of data collection, oftentimes the native data analyzer provided by Google, and the excel files that come with it, are not sufficient for analyzing data, especially for combining and viewing/analyzing data from multiple variable perspectives at once. 

FRP attempts to make analyzing data easier by taking in either the Google-Form output excel sheet or a native Form-editing web link (coming soon!) and graphing that data in easy-to-configure ways using python's matplotlib. 

Because the data retrieved by Google Forms is generally one user per response, the most common use case is to graph data by analyzing the number of people who responded in a certain way. Thus, the only type of graph that FRP currently offers is the bar graph. Furthermore, for the sake of simplicity in analysis, FRP is best used in conjunction with questions that have a relatively small number of possible answers (generally, <10, but depends on the size of the dataset), and not really meant to analyze free-response type questions at all. 

You can use FRP to filter and graph data in many ways, and this tutorial will show you everything FRP has to offer. 

# How to use FRP

To run FRP, simply clone this repository or download the parser.py file located in the repo. FRP has no Python2 compatibility, and is best when run with Python 3.7. 

FRP's dependencies are: 

+ matplotlib
+ numpy
+ requests (currently not yet a dependency, but coming soon)

FRP has only one required input: a json-format file that serves as the configuration for how FRP should parse and analyze data. 

To run FRP, simply use `python3 parser.py [flags] [json filename]`. 

Based on the contents of the JSON, as well as any input flags, FRP may produce output, and may save files to disk. 

## Flags

All flags are optional:

+ `--no-show` When used, FRP will not show the final produced graphs and simply close them when done.
+ `--no-save` When used, will override the JSON configuration file and not save any files to disk.
+ `--verbose` or `-v` When used, will produce more verbose output, such as what files are saved to disk.
+ `--show-others` When used, will output the list of all responses which were deemed "Other" by FRP, based on the answers to questions inputted in the JSON configuration. For more information, see the [Configuring Questions](#configuring-questions) section.

## Configuring the JSON

This section will reference the *example.json* file in this repository. It is paired with the *example.xls* file (also in this repo), and together they will serve as this tutorial's main source of reference. The *example.xls* file was generated from responses to [this form](https://forms.gle/5EihhpiSNxchXT1j6), and the files generated from each example are saved to the `example-outputs` directory of this repo.

### Input/Output
The main level of the JSON contains the basic input/output information that FRP uses., such as the excel filename and its respective sheet name, as well as the output directory of all graphs that will be saved to disk. 

+ `xlsFile` specifies the directory and name of the input Excel file to be given to FRP. It is required. 
+ `sheetName` speficies the specific sheet within *xlsFile* which will be used. It is required.
+ `output-dir` specifies the output directory of all graphs that will be saved to disk. It is optional. If not specified, graphs will be saved to the current working directory. 

FRP does not currently support reading in data from multiple excel files or multiple sheets of any one file. 

*Note*: FRP currently only supports input excel files of type .xls, rather than the newer standard .xlsx. However, note that any .xlsx can be converted to .xls using Microsoft Excel. 

**Example:**

```json
{
    "xlsFile": "example.xls",
    "sheetName": "Sheet1",
    "output-dir": "example-outputs/"
}
```

### Configuring Questions

To inform FRP of all the questions that it needs to analyze, we need to tell it what the exact question name is, what each of the answers are, and also what type of question it is, through this configuration file. All questions are elements of the list under the `questions` subpath. 

```
{
    "xlsFile": "example.xls",
    "sheetName": "Sheet1",
    "output-dir": "example-outputs/",
    "questions": [
        {*question 1*}, 
        {*question 2*},
        ...
    ]
}
```

Each question has the following identifiers: 

+ `question` specifies the **exact** name of a question from the Google Form, which must be placed somewhere in Row 1 of the corresponding excel. It is required.
+ `id` is a string that serves as some sort of identifying tag for this specific question. Although not required, it is highly recommended, because without it this question cannot be used in analysis. 
+ `answers` is a list containing all exact values that FRP should use during analysis. Although not required, it is highly recommended, because all values not included in this list will be considered "other" data that will be discarded, and printed when the `--show-others` flag is enabled.
+ `format` is a string that tells FRP to expect a special format for this question, as detailed below. It is optional - when ommitted, FRP will assume the standard question format. Supported special formats:
    + `select-all` refers to the Multiple-checkboxes type of question, where users can select any number of the given responses.
    + `ranked` refers to a multiple-grid type system where the row describes a ranking system, and the column describes the metrics to be ranked. (For clarity, see question 3 of [this form](https://forms.gle/5EihhpiSNxchXT1j6) and the following example.) *Note that FRP currently does not support the tranposed version of this question, where columns describe the ranking system instead of the row. Furthermore, the ranking system currently only supports being sorted in rank alphabetically.*
    + More options will become available at users' requests. 
+ `optional` is a utility-type boolean. When true, FRP will not error out if it does not find the column labelled with this question. It is optional, and false by default. *Because its use cases are not common, this tutorial does not include it in examples.*

**Example:**

```json
{
    "xlsFile": "example.xls",
    "sheetName": "Sheet1",
    "output-dir": "example-outputs/",
    "questions": [
        {
            "question": "What is your favorite type of pizza?",
            "id": "fav_pizza",
            "answers": ["Pepperoni", "Cheese", "Meatlovers"]
        },
        {
            "question": "How would you rank your seasons? (1 is most favorite, 4 least favorite)",
            "id": "seasons_rank",
            "answers": ["Spring", "Summer", "Autumn", "Winter"],
            "format": "ranked"
        },
        {
            "question": "What breakfast cereals do you like? (select all that apply)",
            "id": "cereal_weeee",
            "answers": ["Honey Nut Cheerios", "Fruit loops", "Lucky Charms"], 
            "format": "select-all"
        }
    ]
}
```

### Configuring Graphs

Once the questions have been inputted into this configuration file, we can use those question IDs and answers to generate graphs. Each graph is an element of the list under the `analysis` subpath. 

```
{
    "xlsFile": "example.xls",
    "sheetName": "Sheet1",
    "output-dir": "example-outputs/",
    "questions": [
        {
            ...
        }
    ],
    "analysis": [
        {*graph 1*}, 
        {*graph 2*},
        ...
    ]
}
```

Each graph must be directly associated with exactly one question, and generally, the number of bars in the bar graph corresponds to the number of answers that said question has, with one-bar-per-question. Each graph has the following identifiers: 

+ `title` is the title of the graph. It is optional - the default is no title. 
+ `x-axis` and `y-axis` are the respective axis labels. They are optional - the default is no label.
+ `save-as` is the graph's saved filename. It is an extension of the `output-dir` optionally specified earlier. It follows the naming and filetype conventions from matplotlib's **savefig** function. It is optional - without it, the graph will not be saved to disk.
+ `config` is a required path which holds the configurations for this specific graph: 
    + 	`id` references the question ID that this graph is directly associated to, from which data for each of the bars of the graph are represented. It is required. 
    +  `percentage` is a boolean flag that specifies whether the bar graph data should be represented as an exact count or as a percentile of the total of every point represented by the graph. It is optional - the default value is false.
    +  `filters` is a list of filters that will be applied to the dataset to limit the amount of data displayed by the graph. It is optional - the default is no filters. FRP supports the following types of filters:
        +  Filtering by another question, with the following identifiers:
            +  `id` refers to the question ID of the question in which data will be filtered. It is required. 
            +  `answers` is a list that represents the specific whitelisted answers of that question that will be allowed through the filter. It is optional; however, if not specified, all data will be filtered out. Answers in the list are not specified by their exact values, but rather by the indices of the answers declared earlier in the JSON questions section. (For further clarification, see the [Examples](#using-filters) section.)

                This filter currently does not allow answers to be blacklisted, only whitelisted. Filters also currently do not support filtering based on ranked-format questions.

        +  More options will become available at users' requests.
+ `bars` is a list of each of the graph's bars' labels. Because graphs will genearlly have one bar per answer, this method allows the user to shorten each labels' length at his own discretion by creating a new label for each answer altogether (answers on Google Forms are sometimes pretty long). It is optional - by default, numbers will be used as labels for each bar. 

Given the configured filters and other miscellaneous information, FRP graphs each bar graph based on the number of users who answered each answer to the question specified at `analysis/config/id`.

**Example**

In this example, we graph the basic idea of how many people like each pizza: 

```
{
    ...
    "analysis": [
        {
            "title": "People's Favorite Pizzas",
            "x-axis": "Pizza type",
            "y-axis": "Number of people who like this pizza",
            "save-as": "everyones_fav_pizzas.jpg",
            "config": {
                "id": "fav_pizza",
                "percentage": false
            },
            "bars": ["Pep.", "Cheese", "Meat"]
        }
    ]
}
```

However, what if we only wanted to see this result for the people who like Honey Nut Cheerios? In that case, we add a filter, and change the other semantic configs accordingly (the changes are bolded):

<pre>
{
    ...
    "analysis": [
        {
            "title": "People<b> Who Like Cheerios</b>'s Favorite Pizzas",
            "x-axis": "Pizza type",
            "y-axis": "Number of people who like this pizza",
            "save-as": "<b>cheerio_lovers</b>_fav_pizzas.jpg",
            "config": {
                "id": "fav_pizza",
                <b>"filters": [
                    {
                        "id": "cereal_weeee",
                        "answers": [0]
                    }
                ],</b>
                "percentage": false
            },
            "bars": ["Pep.", "Cheese", "Meat"]
        }
    ]
}
</pre>

This example outlines the most basic graphing use case. For more complex situations, see the [Examples](#example-use-cases) section.

#### Other identifiers

Specifically for graphing ***ranked-format*** questions, there are two more identifiers within the `analysis/config` subpath that can be used:

+  `ranks` is an identifier to a list which signifies the specific answer ranks that are handled per user, eg. only looking at each user's most or least ranked item, or a variety.
+  `answer` is a unique identifier which changes the x-axis of the graph from being one-answer-per-bar, to one-rank-per-bar. Thus, the number of bars for this graph is equal to the number of ranks specified by that question.

For more information on these additional identifiers, see the [Examples](#ranked-format-specific-identifiers) section.

#### Graphing Sub-plots

One of *matplotlib*'s biggest features is allowing users to plot several sub-plots in the same picture. FRP also leverages this, but in a more organized fashion. 

For each graph, if the graph contains the following three identifiers, then FRP will graph sub-plots instead of the regular graph: 

+ `n-rows` and `n-cols` are positive integers which signify the number of rows and columns, respectively, of sub-plots the graph should contain. 
+ `sub-plots` is a list of all individual configurations for the sub-plots. The number of elements in this list must be equal to `n-rows * n-cols`. When graphing, they will be graphed in standard English reading order, ie. left-to-right, top-to-bottom. 

Then, except for `save-as`, which remains as the graph's optional identifier, all other identifiers are expected to exist (if not optional) within each of the elements of the `sub-plots` list. 

For more detailed information, see the [Examples](#sub-plot-examples) section.


### Example use cases

This section will continue to use the *examples.xls* in this repo. It will also continue to use the same *examples.json* file, except we will add additional graphs to the `analysis` subpath. 

#### Using filters

*To be updated soon*

#### Ranked format-specific identifiers

*To be updated soon*

#### Sub-plot Examples

*To be updated soon*

## Misc.

### Number systems

For all lists in the JSON, FRP will assume a zero-based indexing system.

### Layout of the XLS File

Although this parser is meant to be used in conjunction with Google Forms, which has a set standard for the format of its excel output files, a user could theoretically use FRP to analyze a manually created excel file, as well. These are the guidelines to follow so that FRP can easily maneuver the xls file. 

*To be updated soon*

### Configuring matplotlib

*To be updated soon*

--

# Known bugs


+ ~~Google forms does not always require an email, thus the second column may sometimes be a question - which FRP would always ignore. Current workaround: if the user manually copies the entire second column to a new column, Google Forms will automatically place new responses there - and FRP would see it with no problems.~~ Fixed!
+ When someone chooses to select no answers for a select-all question, their data is not counted in any of the statistics. 

For any questions or to report a bug, please email maplexu2010@gmail.com. Thank you for your help!