import sys
from xlrd import open_workbook
import requests
import json
from pprint import pprint

other_answers = []

def importData(json_file):
    with open(json_file) as inf:
        configs = json.load(inf)
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
    ranked_questions = []
    question_ids = {}
    if (questions := configs.get('questions')) is not None:
        prompts = readRow(sheet, 0)
        for q in questions:
            try:
                question = q['question']
                q_format = q.get('format')
                if q_format == 'ranked':
                    indices = []
                    for i, p in enumerate(prompts):
                        if p[:p.rfind('[') - 1] == question:
                            indices.append(i)
                    if len(indices) == 0:
                        raise ValueError()
                    indices.sort(key=lambda i: prompts[i])
                    ranked_questions.append(indices)
                else:
                    indices = [prompts.index(question)]
                if (q_id := q.get('id')) is not None:
                    question_ids[q_id] = indices[0]
                for i in indices:
                    question_parsing[i] = (q['answers'], q_format)
            except:
                if (optional := q.get('optional')) is not None and optional:
                    continue
                raise ValueError("Did not find question: \n{}".format(q['question']))

    extra_indices = [j for i in ranked_questions for j in i[1:]]
    extra_indices.sort(reverse=True)

    for row in range(1,sheet.nrows):
    # for row in range(1, 2):
        datum = readRow(sheet, row)

        # Additional parsing of inputs
        for n, d in enumerate(datum):
            if d is not None:
                if d == '':
                    datum[n] = -1#'No Answer'
                    print(n)
                    continue
                if len(d) > 2 and d[-2:] == '.0':
                    # Remove trailing .0 from ints that were read in as doubles
                    datum[n] = d[0:-2]
                if (tup := question_parsing.get(n)) is not None:
                    answers, q_format = tup
                    if q_format == 'select-all':
                        l = d.split(',') # Assume select-all-that-apply answers don't have commas
                        if l[-1] == '':
                            l.pop()
                    else: 
                        l = [d]

                    datum[n] = [defaultIndex(answers, i.strip()) for i in l]

        for ranked in ranked_questions:
            datum[ranked[0]] = [datum[i][0] for i in ranked]
        for extra in extra_indices:
            del datum[extra]
        data.append(datum)

    return data, question_parsing, question_ids

def ingestForm(configs):
    raise NotImplementedError("Coming soon")

if __name__ == "__main__":
    data, qs, ids = importData(sys.argv[1])
    pprint(data)
    # pprint(other_answers)