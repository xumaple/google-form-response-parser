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
contact_admin_str = "Please contact the FRP admin for more details."

def plotConfig():
    plt.style.use('seaborn')

class FRPError(Exception):
    '''Base class for other exceptions'''
    pass

class JsonFRPError(FRPError):
    def __init__(self, msg):
        super().__init__('FRP Json ERROR: {}'.format(msg))

class RuntimeFRPError(FRPError):
    def __init__(self, msg):
        super().__init__('FRP ERROR: {}'.format(msg))

class InternalFRPError(FRPError):
    def __init__(self, msg):
        super().__init__('FRP Internal ERROR: {}\n'.format(msg, contact_admin_str))

class Question:
    NO_ANSWER_FLAG = NO_ANSWER_FLAG
    blackListFilter = lambda x: False # Blacklist everything
    whilteListFilter = lambda x: True # Whitelist everything

    def __init__(self, config):
        self.id = config.get('id')
        self.question = config.get('question')
        self.answers = config.get('answers')
        o = config.get('optional')
        self.optional = o is not None and o
        self.userAnswers = {}

    def getAnswerIndex(self, ans):
        try:
            return self.answers.index(ans)
        except ValueError:
            Model.instance().other_answers.append(ans)
            return Question.NO_ANSWER_FLAG

    def configureRow(self, row):
        try:
            self.column = row.index(self.question)
        except ValueError:
            self.errorConfigureRow()

    def add_answer(self, user, row):
        self.check_configured('column')
        try:
            self.add_answer_helper(user, self.getAnswerIndex(row[self.column]))
        except IndexError:
            self.errorAddAnswer()

    def add_answer_helper(self, k, v):
        if self.userAnswers.get(k) is not None:
            self.error("Question received repeat answer key")
        self.userAnswers[k] = v

    def filter(self, f, users):
        func = self.getFilter(f)
        try:
            return list(filter(func, users))
        except:
            self.error("Unable to filter based on question")

    def getFilter(self, f):
        answers = f.get('answers')
        if answers is None or len(answers) == 0:
            return Question.blackListFilter
        return lambda x: self.userAnswers.get(x) in answers

    def score(self, config, users):
        arr = np.zeros(len(self.answers))
        for u in users:
            ans = self.userAnswers.get(u)
            if ans is None:
                self.errorScore(u)
            if ans != Question.NO_ANSWER_FLAG:
                arr[ans] += 1
        return score_adjustments(config, arr), np.sum(arr)

    def check_configured(self, keyword):
        if not hasattr(self, keyword):
            raise InternalFRPError("Question must be configured before answers can be added.")

    def errorConfigureRow(self):
        if not self.optional:
            self.error("Did not find question")

    def errorAddAnswer(self):
        if not self.optional:
            self.error("Did not find answer to question")

    def errorScore(self, user):
        self.error("Question did not receive answer from user {}".format(user))

    def error(self, msg):
        raise RuntimeFRPError("{}: \n{}".format(msg, self.question))

class RankedQuestion(Question):
    def __init__(self, config):
        super().__init__(config)

    def configureRow(self, row):
        self.columns = []
        for i, r in enumerate(row):
            if r[:r.rfind('[') - 1] == self.question:
                self.columns.append(i)
        if len(self.columns) == 0:
            self.errorConfigureRow()
        self.sortConfigureRow(row)

    def sortConfigureRow(self, row):
        self.check_configured('columns')
        self.columns.sort(key=lambda i: row[i])

    def add_answer(self, user, row):
        self.check_configured('columns')
        try:
            ranked_answers = [self.getAnswerIndex(row[c]) for c in self.columns]
            if Question.NO_ANSWER_FLAG in ranked_answers:
                ranked_answers = Question.NO_ANSWER_FLAG
            self.add_answer_helper(user, ranked_answers)
        except IndexError:
            self.errorAddAnswer()

    def getFilter(self, f):
        raise NotImplementedError("Ranked filters are coming soon")

    def score(self, config, users):
        specific_answer_index = config.get('answer')
        if specific_answer_index is not None:
            return self.scoreAnswer(config, users)

        arr = np.zeros(len(self.answers))
        weights, ranks = self.getWeightsAndRanks(config)
        num_answers = 0
        for u in users:
            ans = self.userAnswers[u]
            if ans == Question.NO_ANSWER_FLAG:
                continue
            for i in ranks:
                arr[ans[i]] += (weights[i] if weights is not None else 1)
            num_answers += 1
        return score_adjustments(config, arr), num_answers

    def getWeightsAndRanks(self, config):
        if config.get('ranks') is not None:
            return None, config['ranks']
        return range(num_answers), range(num_answers)

    def scoreAnswer(self, config, users):
        arr = np.zeros(len(self.answers))
        specific_answer_index = config.get('answer')
        for u in users:
            try:
                arr[self.userAnswers[u].index(specific_answer_index)] += 1
            except ValueError:
                pass
        return score_adjustments(config, arr), np.sum(ar)

class SelectAllQuestion(Question):
    def __init__(self, config):
        super().__init__(config)

    def add_answer(self, user, row):
        self.check_configured('column')
        try:
            answers = row[self.column].split(', ') # Assume select-all-that-apply answers don't have commas
            if answers[-1] == '':
                answers.pop()
        except IndexError:
            self.errorAddAnswer()
        indexed_answers = [self.getAnswerIndex(a) for a in answers]
        filtered_answers = list(filter(lambda a: a != Question.NO_ANSWER_FLAG, indexed_answers))
        self.add_answer_helper(user, filtered_answers)

    def getFilter(self, f):
        answers = f.get('answers')
        if answers is None or len(answers) == 0:
            return Question.blackListFilter

        return lambda x: any([a in answers for a in self.userAnswers.get(x)])

    def score(self, config, users):
        arr = np.zeros(len(self.answers))
        num_answers = 0
        for u in users:
            ans = self.userAnswers.get(u)
            if ans is None:
                self.errorScore(u)
            for a in ans:
                arr[a] += 1
            num_answers += 1
        return score_adjustments(config, arr), num_answers

def questionFactory(config):
    form = config.get('format')
    if form == 'ranked':
        return RankedQuestion(config)
    elif form == 'select-all':
        return SelectAllQuestion(config)
    else:
        return Question(config)

class Model:
    __instance = None

    def instance():
        if Model.__instance is None:
            Model(instance=True)
        return Model.__instance

    def __init__(self, instance=False):
        if not instance:
            raise InternalFRPError("Cannot define instance of singleton Model class")
        Model.__instance = self
        self.verbose = VERBOSE
        self.show_others = SHOW_OTHERS

        self.question_map = None
        self.num_users = 0

        self.other_answers = []
        self.saved_files = []

    def getQuestionById(self, q_id):
        if self.question_map is not None:
            q = self.question_map.get(q_id)
            if q is not None:
                return q
        raise JsonFRPError("Did not find Question with ID {}.".format(q_id))

    def importData(self, jsonFileName):
        try:
            with open(jsonFileName) as inf:
                self.configs = json.load(inf)
        except Exception as e:
            raise JsonFRPError('Could not load json file{}\nError message: {}'.format(sys.argv[1], e))
        self.ingestData()

        if self.verbose:
            perr('{} other answers were not documented.'.format(len(self.other_answers)))
        if self.show_others:
            perr('Other answers that were not documented:')
            for a in self.other_answers:
                perr('\t{}'.format(a))

    def ingestData(self):
        self.question_map = {}
        if self.configs.get('xlsFile') is not None:
            self.ingestXLS()
        elif self.configs.get('link') is not None:
            self.ingestForm()
        else: 
            raise JsonFRPError("Did not find xlsFile or link field in JSON to ingest data.")

    def ingestXLS(self):
        filename = self.configs.get('xlsFile')
        sheetName = self.configs.get('sheetName')
        if sheetName is None:
            raise JsonFRPError("Did not find sheetName field to match xlsFile {}.".format(filename))

        book = open_workbook(filename, formatting_info=True)
        sheet = book.sheet_by_name(sheetName)

        questions = self.configs.get('questions')
        if questions is None:
            return

        prompts = readRow(sheet, 0)
        for q_config in questions:
            q = questionFactory(q_config)
            q.configureRow(prompts)
            if self.question_map.get(q.id) is not None:
                raise JsonFRPError("Question ID must be unique, found multiple questions with ID {}.".format(q.id))
            self.question_map[q.id] = q

        for row in range(1,sheet.nrows):
            datum = readRow(sheet, row)
            self.num_users += 1

            for q in self.question_map.values():
                q.add_answer(row, datum)

            if DEBUG_BREAK_EARLY:
                break

    def ingestForm(self):
        raise NotImplementedError("Coming soon")

    def analyzeData(self):
        if self.question_map is None:
            raise InternalFRPError("Data must be ingested before it can be analyzed.")
        plotConfig()
        graphs = self.configs.get('analysis', [])
        generateGraphCopies(graphs)
        for graph in graphs:
            nrows, ncols, sub_plots = graph.get('nrows'), graph.get('ncols'), graph.get('sub-plots')
            if nrows is not None and ncols is not None and sub_plots is not None:
                fig, axes = plt.subplots(nrows=nrows, ncols=ncols)
                while len(axes) != nrows * ncols:
                    axes = [j for i in axes for j in i]

                generateGraphCopies(sub_plots)

                # pprint(sub_plots)

                if len(sub_plots) != nrows * ncols:
                    raise JsonFRPError("With {} rows and {} columns, expected {} sub-plots, found {}.".format(
                        nrows, ncols, nrows * ncols, len(sub_plots)))

                for ax, sp in zip(axes, sub_plots):
                    barGraph(fig, ax, sp)
            else:
                fig, ax = plt.subplots()
                barGraph(fig, ax, graph)

            if SAVE_PLOTS and graph.get('save-as') is not None:
                o = self.configs.get('output-dir', '') + graph['save-as']
                fig.savefig(o)

                if self.verbose:
                    perr('Saving file {} to disk.'.format(o))
                    if o in saved_files:
                        perr('WARNING: File {} was already saved in this program. Overwriting.'.format(o))
                    saved_files.append(o)

        if SHOW_PLOTS:
            plt.show()

def generateGraphCopies(graphsList):
    data = Model.instance()
    for i, graph in enumerate(graphsList):
        config = graph.get('config', {})
        sort_by_id = config.get('sort-by')
        if sort_by_id is None:
            continue
        del graph['config']['sort-by']
        answers = data.getQuestionById(sort_by_id).answers
        for j, ans in enumerate(answers):
            new_graph = add_filter(graph, sort_by_id, [j])
            title = new_graph.get('title', '')
            new_graph['title'] = '{}{}{}'.format(ans.capitalize(), ': ' if title != '' else '', title)
            graphsList.insert(i + j + 1, new_graph)
        del graphsList[i]

def add_filter(graph, id, answers):
    new_graph = copy.deepcopy(graph)
    filters = new_graph['config'].get('filters')
    if filters is None:
        filters = []
        new_graph['config']['filters'] = filters
    filters.append({"id": id, "answers": answers})
    
    return new_graph

def barGraph(fig, ax, graph):
    m = Model.instance()
    conf = graph['config']
    filtered_users = range(1, m.num_users + 1)
    filters = conf.get('filters', [])
    for f in filters:
        f_id = f.get('id')
        if f_id is None:
            raise JsonFRPError("filter must have id")
        filtered_users = m.getQuestionById(f_id).filter(f, filtered_users)
    q_id = conf.get('id')
    if q_id is None:
        raise Exception("Graph config must have ID field.")
    
    scores, num_responses = m.getQuestionById(q_id).score(conf, filtered_users)
    labels = labels = graph['bars'] if graph.get('bars') is not None else range(len(scores))
        
    bars = ax.bar(labels, scores)

    if not graph.get('no-show-responses') == True:
        autolabel(bars, ax, conf.get('percentage'))

    title = graph.get('title')
    if title is not None:
        ax.set_title(title + ' - {} responses'.format(int(num_responses)) if not graph.get('no-show-responses') == True else '')
    elif not graph.get('no-show-responses') == True:
        ax.set_title('{} responses'.format(num_responses))
    ax.set_xlabel(graph.get('x-axis', ''))
    ax.set_ylabel(graph.get('y-axis', ''))

def score_adjustments(config, scores):
    return np.vectorize(lambda x: x / np.sum(scores))(scores) if config.get('percentage') else scores

# Source: https://stackoverflow.com/questions/30228069/how-to-display-the-value-of-the-bar-on-each-bar-with-pyplot-barh
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

def readRow(sheet, row):
    return [str(sheet.cell(row, i).value) for i in range(0, sheet.ncols)]

def perr(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

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
        perr('Usage: python3 parser.py [json config file]')
        exit(1)

    try:
        d = Model.instance()
        d.importData(sys.argv[1])
        # print(ids)
        d.analyzeData()
    except FRPError as e:
        perr()
        perr(e)
        exit(1)
    except Exception as e:
        perr(e)
        perr('Uncaught internal exception.', contact_admin_str)
        exit(1)

# q = RankedQuestion({'answers': [1, 2]})
