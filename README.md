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

+ `--no-show`: When used, FRP will not show the final produced graphs and simply close them when done.
+ `--no-save`: When used, will override the JSON configuration file and not save any files to disk.
+ `--verbose` or `-v`: When used, will produce more verbose output, such as what files are saved to disk.
+ `--show-others`: When used, will output the list of all responses which were deemed "Other" by FRP, based on the answers to questions inputted in the JSON configuration. For more information, see the [Configuring Questions](#configuring-questions) section.

## Configuring the JSON

This section will reference the *example.json* file in this repository. It is paired with the *example.xls* file (also in this repo), and together they will serve as this tutorial's main source of reference. The *example.xls* file was generated from responses to [this form](https://forms.gle/D3rAS5g1ABf65N3S8), and the files generated from each example are saved to the `example-outputs` directory of this repo.

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

Each question has the following fields: 

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

Each graph must be directly associated with exactly one question, and generally, the number of bars in the bar graph corresponds to the number of answers that said question has, with one-bar-per-question. The order that the bars appear in the graph therefore match the order answers are declared in the *questions* configuration, from left to right. Each graph has the following fields: 

+ `title` is the title of the graph. It is optional - the default is no title. 
+ `x-axis` and `y-axis` are the respective axis labels. They are optional - the default is no label.
+ `save-as` is the graph's saved filename. It is an extension of the `output-dir` optionally specified earlier. It follows the naming and filetype conventions from matplotlib's **savefig** function. It is optional - without it, the graph will not be saved to disk.
+ `config` is a required path which holds the configurations for this specific graph: 
    + 	`id` references the question ID that this graph is directly associated to, from which data for each of the bars of the graph are represented. It is required. 
    +  `percentage` is a boolean flag that specifies whether the bar graph data should be represented as an exact count or as a percentile of the total of every point represented by the graph. It is optional - the default value is false.
    +  `filters` is a list of filters that will be applied to the dataset to limit the amount of data displayed by the graph. It is optional - the default is no filters. FRP supports the following types of filters:
        +  Filtering by another question, with the following fields:
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
        },
        ...
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
        },
        ...
    ]
}
</pre>

Both of the graphs generated from this example can be found in the [output-examples folder](https://github.com/xumaple/google-form-response-parser/tree/master/example-outputs). This example outlines the most basic graphing use case. For more complex situations, see the [Examples](#example-use-cases) section.

#### Other fields

Specifically for graphing ***ranked-format*** questions, there are two more fields within the `analysis/config` subpath that can be used:

+  `ranks` is an field to a list which signifies the specific answer ranks that are handled per user, eg. only looking at each user's most or least ranked item, or a variety.
+  `answer` is a unique field which changes the x-axis of the graph from being one-answer-per-bar, to one-rank-per-bar. Thus, the number of bars for this graph is equal to the number of ranks specified by that question.

Only one of these fields can be used for each ranked-format graph, and they are otherwise optional. Including them in any non-ranked-format graph will not produce any effect. For more information on these additional fields, see the [Examples](#ranked-format-specific-fields) section.

#### Graphing Sub-plots

One of *matplotlib*'s biggest features is allowing users to plot several sub-plots in the same picture. FRP also leverages this, but in a more organized fashion. 

For each graph, if the graph contains the following three fields, then FRP will graph sub-plots instead of the regular graph: 

+ `n-rows` and `n-cols` are positive integers which signify the number of rows and columns, respectively, of sub-plots the graph should contain. 
+ `sub-plots` is a list of all individual configurations for the sub-plots. The number of elements in this list must be equal to `n-rows * n-cols`. When graphing, they will be graphed in standard English reading order, ie. left-to-right, top-to-bottom. 

Then, except for `save-as`, which remains as the graph's optional field, all other fields are expected to exist (if not optional) within each of the elements of the `sub-plots` list. 

For more detailed information, see the [Examples](#sub-plot-examples) section.


### Example use cases

This section will continue to use the *examples.xls* in this repo, drawn from the [google form](https://forms.gle/D3rAS5g1ABf65N3S8) (which we strongly recommend taking a look at before looking at these more complex examples). It will also continue to use the same *examples.json* file, except we will add additional graphs to the `analysis` subpath. As before, all changes will be in bold for easier reading.

#### Using filters

What if we wanted to see how people like pizza, but only if they like either Cheerios or Lucky Charms? This is a case in which we can use multiple answers in the filter, such that having either answer allows the user to be whitelisted through the filter: 

<pre>
{
    ...
            "save-as": "cheerio_<b>or_lucky_</b>lovers_fav_pizzas.jpg",
            ...
                "filters": [
                    {
                        "id": "cereal_weeee",
                        <b>"answers": [0, 2]</b>
                    }
    ...
}
</pre>

However, what if we wanted to see how people like pizza, but only if they like Cheerios ***and*** Lucky Charms? In this case, the single filter doesn't work, so we instead need two filters of the same question, to indirectly perform a logical *and* as a filter:

<pre>
{
    ...
            "save-as": "cheerio_<b>and</b>_lucky_lovers_fav_pizzas.jpg",
            ...
                "filters": [
                    {
                        "id": "cereal_weeee",
                        <b>"answers": [0]</b>
                    }, 
                    <b>{
                        "id": "cereal_weeee",
                        <b>"answers": [2]</b>
                    }</b>
    ...
}
</pre>

Although we won't show an example of this, do note that one graph can definitely have multiple filters that each filter based on different questions - they don't have to all refer to one question like this example does. (Because this is a simple dataset, we simply don't have enough questions for more complex filtering.)

#### Ranked format-specific fields

This section refers to fields which help specifically with visualizing ranked-format data: the `ranks` and `answer` field. Because we can only work with ranked-format questions, we will definitely be working with the example question regarding people's favorite seasons; however, if we desire to, we can still choose to filter our data based on other non-ranked-format questions.

##### Using the *ranks* field

Suppose I want to see each person's least favorite season. The `ranks` field is perfect for this use case: 

<pre>
{
    ...
    "analysis": [
        {
            "title": "Least Favorite Seasons",
            "x-axis": "Season",
            "y-axis": "Number of people who hate this season",
            "save-as": <b>"least_favorite_seasons.jpg"</b>,
            "config": {
                "id": <b>"seasons_rank"</b>,
                <b>"ranks": [3]</b>
            },
            "bars": <b>["Spring", "Summer", "Autumn", "Winter"]</b>
        },
        ...
    ]
}
</pre>

Notice that the `ranks` field is a list, so for example, if we wanted to see a combination of people's preferences (eg. last two choices, or first and last), then we just need to add other indices to the list (eg. [2, 3] or [0, 3], respectively). 

##### Using the *answer* field

Suppose I want to see where people tended to rank Summer among their seasons. That's what the `answer` field is for: 

<pre>
{
    ...
    "analysis": [
        {
            "title": "How Much People Like Summer",
            "x-axis": "People's reactions",
            "y-axis": "Number of people who like summer this much",
            "save-as": <b>"summer.jpg"</b>,
            "config": {
                "id": "seasons_rank",
                <b>"answer": 1</b>
            },
            "bars": <b>["Love it!", "Pretty good", "Meh", "I hate it :("]</b>
        },
        ...
    ]
}
</pre>

Notice that the `bars` field is no longer listing out labels for answers to the question, but rather rankings (this is described in [Other fields](#other fields)). Also notice that the `answer` field is a single value, so FRP cannot show how people rank multiple answers at once, as that does not have much plausible semantic value (but, if this is a requested feature, it can be implemented!).

Although we won't show an example of this, each of these ranked-format fields can still be used in conjunction with filters of non-ranked questions. Using any such filters simply filters out data points as specified by each filter, before either of these fields analyze the data used in the graph.  

#### Sub-plot Examples

Sub-plots are useful when the user desires graphs to be side-by-side. Oftentimes, this may be because they want to compare similar data. As an example, suppose I have the previously drawn data of people's least favorite season, but I want to see how this data varies based on people's favorite pizza. In that case, we can use subplots, with the addition of filters, to draw our different sub-plots: 

(Note - instead of bolding everything new, which is everything, the bolded parts will be the important parts - the rest is a lot of copy/paste)

<pre>
{
    ...
    "analysis": [
        {
            <b>"nrows": 2,
            "ncols": 2,
            "save-as": "least_favorite_seasons_by_pizza.jpg",
            "sub-plots":</b> [
                {
                    "title": "Least Favorite Seasons",
                    "x-axis": "Season",
                    "y-axis": "Number of people who hate this season",
                    "config": {
                        "id": "seasons_rank",
                        "ranks": [3]
                    },
                    "bars": ["Spring", "Summer", "Autumn", "Winter"]
                }, 
                {
                    "title": "Least Favorite Seasons for Pepperoni Lovers",
                    "x-axis": "Season",
                    "y-axis": "Number of people who hate this season",
                    "config": {
                        "id": "seasons_rank",
                        "ranks": [3],
                        <b>"filters": [
                            {
                                "id": "fav_pizza",
                                "answers": [0]
                            }
                        ]</b>
                    },
                    "bars": ["Spring", "Summer", "Autumn", "Winter"]
                },
                {
                    "title": "Least Favorite Seasons for Cheese Lovers",
                    "x-axis": "Season",
                    "y-axis": "Number of people who hate this season",
                    "config": {
                        "id": "seasons_rank",
                        "ranks": [3],
                        "filters": [
                            {
                                "id": "fav_pizza",
                                <b>"answers": [1]</b>
                            }
                        ]
                    },
                    "bars": ["Spring", "Summer", "Autumn", "Winter"]
                },
                {
                    "title": "Least Favorite Seasons for Meat Lovers",
                    "x-axis": "Season",
                    "y-axis": "Number of people who hate this season",
                    "config": {
                        "id": "seasons_rank",
                        "ranks": [3],
                        "filters": [
                            {
                                "id": "fav_pizza",
                                <b>"answers": [2]</b>
                            }
                        ]
                    },
                    "bars": ["Spring", "Summer", "Autumn", "Winter"]
                }
            ]
        },
        ...
    ]
}
</pre>

To see what this graph looks like, visit the [example-outputs folder](https://github.com/xumaple/google-form-response-parser/blob/master/example-outputs/least_favorite_seasons_by_pizza.jpg). Note that this is just a 2-by-2 subplot, and our JSON is already extremely long and full of long sections that were mainly copy-pasted, except for a line or two or change. For larger subplots, the JSON would easily become unmanageable

Thus, there is one shortcut field that can be used to change: the `sort-by`field, which takes in the question ID of the question to be varied-by-answer. It takes the place of the filter that specifically limits to one of the answers to said question, and is a field within the `analysis/sub-plot/config` subpath. Take a look at the following example: 

(For fun, let's also transform the sub-plots into a different shape)

<pre>
{
    ...
    "analysis": [
        {
            "nrows": 2,
            "ncols": 2,
            "save-as": "least_favorite_seasons_by_pizza<b>_with_shortcut</b>.jpg",
            "sub-plots": [
                {
                    "title": "Least Favorite Seasons",
                    "x-axis": "Season",
                    "y-axis": "Number of people who hate this season",
                    "config": {
                        "id": "seasons_rank",
                        "ranks": [3]
                    },
                    "bars": ["Spring", "Summer", "Autumn", "Winter"]
                }, 
                {
                    <b>"title": "Least Favorite Seasons"</b>,
                    "x-axis": "Season",
                    "y-axis": "Number of people who hate this season",
                    "config": {
                        "id": "seasons_rank",
                        "ranks": [3],
                        <b>"sort-by": "fav_pizza",
                        "filters": []</b>
                    },
                    "bars": ["Spring", "Summer", "Autumn", "Winter"]
                }
            ]
        },
        ...
    ]
}
</pre>

Comparing [this graph](https://github.com/xumaple/google-form-response-parser/blob/master/example-outputs/least_favorite_seasons_by_pizza_with_shortcut.jpg) with the previous, although the subplots are in a different shape (1x4 instead of 2x2), the graphs themselves are the same, but this version that uses the shortcut is much shorter. In fact, the shortcut is only being used in the latter of the two sub-plots in this example - the former is just a regular sub-plot. This shortcut is super useful! Some notes/caveats:

+ The restriction that `nrows * ncols` is equal to the number of elements in sub_plots still applies. When the sort-by shortcut is used, FRP is actually automatically generating the other sub-plots before checking this restriction. 
+ When the `sort-by` field is used, FRP will always generate 1 sub-plot per answer for the question specified. If the user wants to use a different algorithm to plot the sub-plots, it is not supported by this shortcut. 
+ FRP will always generate the sub-plots in order of the answers specifed in the JSON file. Thus, when they are plotted into the plot as a whole, they will also follow this order. If the user wants to use a different order, it is not supported by this shortcut. 
+ Note that using the `sort-by` field does not disqualify this sub-plot from using other filters. However, any such filters used in the same sub-plot as the `sort-by` field will be used in all sub-plots automatically that FRP generates from this field, as well. 
+ Note that the titles for each respective sub-plot is the only significant  difference between the two examples. This is because FRP automatically appends the answer used to the beginning of the sub-plot, for clarity and differentiation of the sub-plots. FRP does not currently support turning off this feature, or using custom titles/axis-labels for each automatically generated sub-plot. 

Happy plotting!

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
+ Depending on the default size of matplotlib figures, sometimes axes/titles will overlap, especially when sub-plots are being used, creating very messy graphs.

For any questions or to report a bug, please email maplexu2010@gmail.com. Thank you for your help!