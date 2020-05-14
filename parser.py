import sys
from xlrd import open_workbook
import requests
import json
from pprint import pprint

# class Question:
#     def __init__(self, question, answers):
#         self.question = question
#         self.answers = answers


# class Configs:
#     __instance = None

#     __xlsFile = None
#     __sheetName = None
#     __link = None

#     questions = []

#     def setXls(self, _xls):
#         self.__xlsFile = _xls
#     def getXls(self):
#         return self.__xlsFile
#     def setSheet(self, _sheet):
#         self.__sheetName = _sheet
#     def getSheet(self):
#         return self.__sheetName
#     def setLink(self, _link):
#         self.__link = _link
#     def getLink(self):
#         return self.__link
#     def addQuestion(self, q):
#         if isinstance(q, Question):
#             self.questions.append(q)
#         else:
#             print('Error: Cannot add question of type', type(q))
#     def addQuestions(self, qs):
#         for q in q:
#             self.addQuestion(q)

#     def instance():
#         if Configs.__instance is None:
#             Configs()
#         return Configs.__instance

#     def __init__(self):
#         Configs.__instance = self

# config = Configs.instance()

other_answers = []

def importData(json_file):
    with open(json_file) as inf:
        configs = json.load(inf)
    import pprint
    pprint.pprint(configs)
    if configs.get('xlsFile') is not None:
        return ingestXLS(configs)
    else:
        ingestForm(configs)

def readRow(sheet, row):
    return [str(sheet.cell(row, i).value) for i in range(2, sheet.ncols)]

def defaultIndex(arr, val, default=None):
    try:
        return arr.index(val)
    except ValueError:
        other_answers.append(val)
        return val if default is None else default

def ingestXLS(configs):
    filename = configs.get('xlsFile')
    sheetName = configs.get('sheetName')
    print(filename, sheetName)
    book = open_workbook(filename, formatting_info=True)
    sheet = book.sheet_by_name(sheetName)

    data = []

    question_parsing = {}
    if (questions := configs.get('questions')) is not None:
        prompts = readRow(sheet, 0)
        for q in questions:
            try:
                index = prompts.index(q['question'])
                select = q.get('select-all')
                if select is None:
                    select = False
                question_parsing[index] = (q['answers'], select)
            except:
                if (optional := q.get('optional')) is not None and optional:
                    continue
                raise ValueError("Did not find question: \n{}".format(q['question']))

    for row in range(1,sheet.nrows):
    # for row in range(1, 2):
        datum = readRow(sheet, row)

        # Additional parsing of inputs
        for n, d in enumerate(datum):
            if d is not None:
                if d is '':
                    datum[n] = -1#'No Answer'
                    continue
                if len(d) > 2 and d[-2:] == '.0':
                    # Remove trailing .0 from ints that were read in as doubles
                    datum[n] = d[0:-2]
                if (tup := question_parsing.get(n)) is not None:
                    answers, select_all = tup
                    if select_all:
                        l = d.split(',') # Assume select-all-that-apply answers don't have commas
                        if l[-1] == '':
                            l.pop()
                    else: 
                        l = [d]

                    datum[n] = [defaultIndex(answers, i.strip()) for i in l]

        data.append(datum)

    # sort by location (1) then name (0)
    #data = sorted(data, key=itemgetter(1,0))
    return data

def ingestForm(configs):
    raise NotImplementedError("Coming soon")

if __name__ == "__main__":
    print(importData(sys.argv[1]))
    pprint(other_answers)