import sys
from xlrd import open_workbook
import requests
import json
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from pprint import pprint

SHOW_PLOTS = False
SAVE_PLOTS = True
DEBUG_BREAK_EARLY = False
NO_ANSWER_FLAG = 'NO_ANSWER'

other_answers = []

def importData(configs):
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
    # print(filename, sheetName)
    book = open_workbook(filename, formatting_info=True)
    sheet = book.sheet_by_name(sheetName)

    data = []

    question_parsing = {}
    ranked_questions = []
    question_ids = {}
    questions = configs.get('questions')
    if questions is not None:
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
                q_id = q.get('id')
                if q_id is not None:
                    question_ids[q_id] = indices[0]
                    if q.get('answers') is None:
                        continue
                for i in indices:
                    question_parsing[i] = (q['answers'], q_format)
            except:
                optional = q.get('optional')
                if optional is not None and optional:
                    continue
                raise ValueError("Did not find question: \n{}".format(q['question']))

    extra_indices = [j for i in ranked_questions for j in i[1:]]
    extra_indices.sort(reverse=True)

    for row in range(1,sheet.nrows):
        datum = readRow(sheet, row)

        # Additional parsing of inputs
        for n, d in enumerate(datum):
            if d is not None:
                if d == '':
                    datum[n] = NO_ANSWER_FLAG
                    # print(n)
                    continue
                if len(d) > 2 and d[-2:] == '.0':
                    # Remove trailing .0 from ints that were read in as doubles
                    datum[n] = int(d[0:-2])
                tup = question_parsing.get(n)
                if tup is not None:
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

        if DEBUG_BREAK_EARLY:
            break

    for extra in extra_indices:
        del question_parsing[extra]
    return data, question_parsing, question_ids

def ingestForm(configs):
    raise NotImplementedError("Coming soon")

def plotConfig():
    # plt.axis('on')
    plt.style.use('seaborn')

def analyzeData(configs, data, question_answers, ids):
    # import numpy as np
    # import matplotlib.pyplot as plt
    # height = [3, 12, 5, 18, 45]
    # bars = ('A', 'B', 'C', 'D', 'E')
    # y_pos = np.arange(len(bars))
    # plt.bar(y_pos, height, color=(0.2, 0.4, 0.6, 0.6))
     
    # # Custom Axis title
    # plt.xlabel('title of the xlabel', fontweight='bold', color = 'orange', fontsize='17', horizontalalignment='center')
    # plt.show()
    # return
    plotConfig()
    graphs = configs.get('analysis')
    if graphs is None:
        return
    for graph in graphs:
        fig, ax = plt.subplots()
        conf = graph['config']
        filtered_data = data
        filters = conf.get('filters')
        if filters is not None:
            for f in filters:
                question_index = ids[f['id']]
                form = question_answers[ids[f['id']]][1]
                filtered_data = filter(lambda datum: filter_data(datum[question_index], f, form), filtered_data)
            filtered_data = list(filtered_data)
        form = question_answers[ids[conf['id']]][1]
        if form == 'ranked':
            scores, num_responses = score_ranked(conf, filtered_data, question_answers, ids)
        elif form == 'select-all':
            scores, num_responses = score_select_all(conf, filtered_data, question_answers, ids)
        elif form is None:
            scores, num_responses = score_regular(conf, filtered_data, question_answers, ids)
        else:
            NotImplementedError("no such type")
            # print(scores)
        labels = range(len(scores))
        if graph.get('bars') is not None:
            labels = graph['bars']
        # print(labels, scores)
        bars = ax.bar(labels, scores)
        if not graph.get('no-show-responses') == True:
            autolabel(bars, ax, conf.get('percentage'))

        title, x, y = graph.get('title'), graph.get('x-axis'), graph.get('y-axis')
        if title is not None:
            ax.set_title(title + ' - {} responses'.format(num_responses) if not graph.get('no-show-responses') == True else '')
        if x is not None:
            ax.set_xlabel(x)
        if y is not None:
            ax.set_ylabel(y)

        if SAVE_PLOTS and graph.get('save-as') is not None:
            output_dir = configs.get('output-dir')
            if output_dir is None:
                output_dir = ''
            fig.savefig(output_dir + graph['save-as'])
    if SHOW_PLOTS:
        plt.show()

def score_ranked(config, data, question_answers, ids):
    answers = get_answers(config, data)
    num_answers = len(answers[0])
    scores = np.zeros(num_answers)

    specific_answer_index = config.get('answer')
    if specific_answer_index is not None:
        # print(answers)
        for user_answers in answers:
            try:
                scores[user_answers.index(specific_answer_index)] += 1
            except ValueError:
                pass
        return score_adjustments(config, scores), len(answers)

    weighted, ranks = True, range(num_answers)
    if config.get('ranks') is not None:
        ranks = config.get('ranks')
        weighted = False
    for user_answers in answers:
        for i in ranks:
            scores[user_answers[i]] += (i if weighted else 1)

    if weighted:
        return score_adjustments(config, np.vectorize(lambda x: num_answers * len(answers) - x)(scores)), len(answers)
    return score_adjustments(config, scores), len(answers)

def score_select_all(config, data, question_answers, ids):
    answers = get_answers(config, data)
    # print(question_answers[ids[config['id']]][0])
    num_answers = len(question_answers[ids[config['id']]][0])
    scores = np.zeros(num_answers)

    for user_answers in answers:
        # # scores[tuple(list(filter(lambda x: x >= 0 and x < num_answers, user_answers)))] += 1 # TODO
        # try:
        #     scores[tuple(user_answers)] += 1
        # except:
        #     pass

        for a in user_answers:
            try:
                scores[a] += 1
            except:
                pass
    return score_adjustments(config, scores), len(answers)

def score_regular(config, data, question_answers, ids):
    answers = get_answers(config, data)
    num_answers = len(question_answers[ids[config['id']]][0])
    scores = np.zeros(num_answers)

    for a in answers:
        try:
            scores[a[0]] += 1
        except:
            pass

    return score_adjustments(config, scores), len(answers)
    

def get_answers(config, data):
    index = ids[config['id']]
    answers = [data[i][index] for i in range(len(data))]
    return list(filter(lambda x: x != NO_ANSWER_FLAG, answers))

def score_adjustments(config, scores):
    return np.vectorize(lambda x: x / np.sum(scores))(scores) if config.get('percentage') else scores

def autolabel(rects, ax, is_percentage):
    """Attach a text label above each bar in *rects*, displaying its height."""
    for rect in rects:
        height = rect.get_height()
        s = '{:.0f}'.format(height)
        if is_percentage:
            s = '{:.2f}%'.format(height * 100)
        ax.annotate(s,
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom')

def filter_data(datum, f, form):
    answers = f.get('answers')
    if answers is None or len(answers) == 0:
        return False
    if form == 'ranked':
        raise NotImplementedError("Coming soon")
    return datum[0] in f.get('answers')

if __name__ == "__main__":
    with open(sys.argv[1]) as inf:
        configs = json.load(inf)
    data, qs, ids = importData(configs)
    # pprint(ids)
    analyzeData(configs, data, qs, ids)
    # pprint(other_answers)