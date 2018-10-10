import flask
from flask import Flask, g, render_template, request, Response

from StringIO import StringIO
import csv

import scorify
from scorify import scoresheet, datafile, scorer
from scorify.utils import pp

app = Flask(__name__, static_folder='public', template_folder='templates')

print("Hello I am in here")

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/score', methods=('GET', 'POST'))
def score():
    score_io = StringIO(request.form['scoresheet'])
    score_csv = unicode_csv_reader(score_io)
    ss = scoresheet.Reader(score_csv).read_into_scoresheet()
    if ss.has_errors():
        return "Errors in scoresheet\n: {}".format("\n".join(ss.errors))
    data_io = StringIO(unicode(request.form['data'].encode('ascii', errors='ignore')))
    data_csv = unicode_csv_reader(data_io)
    try:
        data_for_scoring = datafile.Datafile(data_csv, ss.layout_section, ss.rename_section)
        data_for_scoring.read()
        scored = scorer.Scorer.score(data_for_scoring, ss.transform_section, ss.score_section)
        scorer.Scorer.add_measures(scored, ss.measure_section)
    except Exception as exc:
        return Response(exc, mimetype='text/plain')
    
    data_io = make_data_io(scored)
    return Response(data_io.getvalue(), mimetype='text/plain')


def unicode_csv_reader(utf8_data, dialect=csv.excel, **kwargs):
    csv_reader = csv.reader(utf8_data, dialect=dialect, **kwargs)
    for row in csv_reader:
        yield [unicode(cell, 'utf-8') for cell in row]


def make_data_io(scored_data, nans_as='NaN'):
    out_io = StringIO()
    out_csv = csv.writer(out_io)
    out_csv.writerow(scored_data.header)
    for row in scored_data:
        rl = [pp(row[h], none_val=nans_as) for h in scored_data.header]
        out_csv.writerow(rl)
    return out_io
  
if __name__ == "__main__":
    app.run()
