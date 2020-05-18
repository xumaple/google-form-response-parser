import sys
from xlrd import open_workbook
import requests
import json
import copy
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from pprint import pprint

SHOW_PLOTS = True
SAVE_PLOTS = True
VERBOSE = False
SHOW_OTHERS = False
DEBUG_BREAK_EARLY = False
NO_ANSWER_FLAG = '_'

def plotConfig():
    plt.style.use('seaborn')

other_answers = []
saved_files = []

def importData(configs):
    if configs.get('xlsFile') is not None:
        ret = ingestXLS(configs)
    else:
        ret = ingestForm(configs)

    if VERBOSE:
        print('{} other answers were not documented.'.format(len(other_answers)))
    if SHOW_OTHERS:
        print('Other answers that were not documented:')
        for a in other_answers:
            print('\t{}'.format(a))

    return ret

def readRow(sheet, row):
    return [str(sheet.cell(row, i).value) for i in range(1, sheet.ncols)]

def defaultIndex(arr, val, default=None):
    if isinstance(val, str):
        val = val.strip()
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
                raise ValueError("Did not find answer to question: \n{}".format(q['question']))

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
                    d = int(d[0:-2])
                    datum[n] = d
                tup = question_parsing.get(n)
                if tup is not None:
                    answers, q_format = tup
                    if q_format == 'select-all':
                        l = d.split(',') # Assume select-all-that-apply answers don't have commas
                        if l[-1] == '':
                            l.pop()
                    else: 
                        l = [d]

                    datum[n] = [defaultIndex(answers, i) for i in l]

        for ranked in ranked_questions:
            datum[ranked[0]] = [datum[i][0] for i in ranked]
        # for extra in extra_indices:
            # del datum[extra]
            # for i in range(extra, len(datum)):
            #     print(datum)
            #     datum[i] -= 1
        data.append(datum)

        if DEBUG_BREAK_EARLY:
            break

    for extra in extra_indices:
        del question_parsing[extra]
    return data, question_parsing, question_ids

def ingestForm(configs):
    raise NotImplementedError("Coming soon")

def analyzeData(configs, data, question_answers, ids):
    plotConfig()
    graphs = configs.get('analysis')
    if graphs is None:
        return
    for graph in graphs:
        nrows, ncols, sub_plots = graph.get('nrows'), graph.get('ncols'), graph.get('sub-plots')
        if nrows is not None and ncols is not None and sub_plots is not None:
            fig, axes = plt.subplots(nrows=nrows, ncols=ncols)
            # print(type(axes))
            while len(axes) != nrows * ncols:
                axes = [j for i in axes for j in i]
            
            for i, sub in enumerate(sub_plots):
                c = sub.get('config')
                if c is not None:
                    sort_by_id = c.get('sort-by')
                    if sort_by_id is None:
                        continue
                    del sub['config']['sort-by']
                    answers = question_answers[ids[sort_by_id]][0]
                    num_answers = len(answers)
                    for ans in range(num_answers):
                        sub_plots.insert(i + ans + 1, add_filter(sub, sort_by_id, ans, answers[ans]))
                    del sub_plots[i]

            if len(sub_plots) != nrows * ncols:
                # TODO error
                print('err')
        else:
            fig, axes = plt.subplots()
            sub_plots = [graph]
            axes = [axes]

        for ax, sp in zip(axes, sub_plots):
            conf = sp['config']
            filtered_data = data
            filters = conf.get('filters')
            if filters is not None:
                # pprint(filtered_data)
                for f in filters:
                    question_index = ids[f['id']]
                    form = question_answers[ids[f['id']]][1]
                    filtered_data = filter(lambda datum: filter_data(datum[question_index], f, form), filtered_data)
                filtered_data = list(filtered_data)
                # print('\n', filtered_data)
            form = question_answers[ids[conf['id']]][1]
            if form == 'ranked':
                scores, num_responses = score_ranked(conf, filtered_data, question_answers, ids)
            elif form == 'select-all':
                scores, num_responses = score_select_all(conf, filtered_data, question_answers, ids)
            elif form is None:
                scores, num_responses = score_regular(conf, filtered_data, question_answers, ids)
            else:
                NotImplementedError("no such type")
            labels = range(len(scores))
            if sp.get('bars') is not None:
                labels = sp['bars']
            # print(labels, scores)
            bars = ax.bar(labels, scores)
            if not sp.get('no-show-responses') == True:
                autolabel(bars, ax, conf.get('percentage'))

            title, x, y = sp.get('title'), sp.get('x-axis'), sp.get('y-axis')
            if title is not None:
                ax.set_title(title + ' - {} responses'.format(num_responses) if not sp.get('no-show-responses') == True else '')
            if x is not None:
                ax.set_xlabel(x)
            if y is not None:
                ax.set_ylabel(y)

        if SAVE_PLOTS and graph.get('save-as') is not None:
            output_dir = configs.get('output-dir')
            if output_dir is None:
                output_dir = ''
            o = output_dir + graph['save-as']
            fig.savefig(o)

            if VERBOSE:
                print('Saving file {} to disk.'.format(o))
                if o in saved_files:
                    print('WARNING: File {} was already saved in this program. Overwriting.'.format(o))
                saved_files.append(o)

    if SHOW_PLOTS:
        plt.show()

def score_ranked(config, data, question_answers, ids):
    answers = get_answers(config, data)
    num_answers = len(answers[0])
    scores = np.zeros(num_answers)

    specific_answer_index = config.get('answer')
    if specific_answer_index is not None:
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
    # pprint(data)
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
    # print(datum)
    answers = f.get('answers')
    if answers is None or len(answers) == 0:
        return False
    if form == 'ranked':
        raise NotImplementedError("Coming soon")
    return datum[0] in f.get('answers')

def add_filter(sub_plot, id, answer_num, answer):
    new_sub_plot = copy.deepcopy(sub_plot)
    filters = new_sub_plot['config'].get('filters')
    if filters is None:
        filters = []
        new_sub_plot['config']['filters'] = filters
    filters.append({"id": id, "answers": [answer_num]})
    title = new_sub_plot.get('title', '')
    new_sub_plot['title'] = '{}{}{}'.format(answer.capitalize(), ': ' if title != '' else '', title)
    return new_sub_plot

if __name__ == "__main__":
    if '--no-show' in sys.argv:
        SHOW_PLOTS = False
        del sys.argv[sys.argv.index('--no-show')]
    if '--no-save' in sys.argv:
        SAVE_PLOTS = False
        del sys.argv[sys.argv.index('--no-save')]
    if '--verbose' in sys.argv:
        VERBOSE = True
        del sys.argv[sys.argv.index('--verbose')]
    if '-v' in sys.argv:
        VERBOSE = True
        del sys.argv[sys.argv.index('-v')]
    if '--show-others' in sys.argv:
        SHOW_OTHERS = True
        del sys.argv[sys.argv.index('--show-others')]

    if len(sys.argv) != 2:
        print('Usage: python3 parser.py [json config file]')
        exit(1)
    try:
        with open(sys.argv[1]) as inf:
            configs = json.load(inf)
    except:
        print('ERROR: Could not load json file', sys.argv[1])
        exit(1)
    data, qs, ids = importData(configs)
    print(ids)
    analyzeData(configs, data, qs, ids)