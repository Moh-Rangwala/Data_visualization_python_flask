# Name: Mohammad Firoz Rangwala
# ID: 1001872492

import os
from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import fields, validators
from werkzeug.utils import secure_filename
import numpy as np

import helper

app = Flask(__name__, static_folder='assets')
Bootstrap(app)

# config
app.config['host'] = '0.0.0.0'
app.config['port'] = int(os.getenv('PORT', '8080'))
app.config['SECRET_KEY'] = '1001872492'
app.config['allowed_csv_ext'] = {'csv', 'txt'}
app.config['project_dir'] = os.path.abspath(os.path.dirname(__file__))
app.config['csv_upload_dir'] = os.path.join(app.config['project_dir'], 'assets')
app.config['db_path'] = os.path.join(app.config['csv_upload_dir'], 'db.sqlite')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////' + app.config['db_path']

db = SQLAlchemy(app)

# db earthquake
class EarthquakeDB(db.Model):
    time = db.Column(db.DateTime, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    depth = db.Column(db.Float, nullable=False)
    mag = db.Column(db.Float, nullable=True)
    magType = db.Column(db.String(10), nullable=True)
    nst = db.Column(db.Integer, nullable=True)
    gap = db.Column(db.Float, nullable=True)
    dmin = db.Column(db.Float, nullable=True)
    rms = db.Column(db.Float, nullable=False)
    net = db.Column(db.String(5), nullable=False)
    id = db.Column(db.String(15),
                   nullable=False,
                   unique=True,
                   primary_key=True)
    updated = db.Column(db.DateTime, nullable=False)
    place = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(15), nullable=False)
    horizontalError = db.Column(db.Float, nullable=True)
    depthError = db.Column(db.Float, nullable=True)
    magError = db.Column(db.Float, nullable=True)
    magNst = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(10), nullable=False)
    locationSource = db.Column(db.String(5), nullable=False)
    magSource = db.Column(db.String(5), nullable=False)

    # flask forms

class FileForm(FlaskForm):
    file = fields.FileField('Earthquake Dataset File')
    submit = fields.SubmitField('Submit')


class StatForm(FlaskForm):
    low = fields.IntegerField(
        'Low Magnitude', validators=[validators.NumberRange(min=0, max=8)])
    high = fields.IntegerField(
        'High Magnitude', validators=[validators.NumberRange(min=0, max=8)])
    method = fields.SelectField('Visualization Method',
                                choices=[('bar', 'Bar'), ('pie', 'Pie')])
    submit = fields.SubmitField('Submit')


class CompareForm(FlaskForm):
    loc1_latitude = fields.FloatField(
        'Latitude of Location 1 (Anchorage is 61)',
        validators=[validators.NumberRange(min=-90, max=90)])
    loc1_longitude = fields.FloatField(
        'Longitude of Location 1 (Anchorage is -150)',
        validators=[validators.NumberRange(min=-180, max=180)])
    loc2_latitude = fields.FloatField(
        'Latitude of Location 2 (Dallas is 32.8)',
        validators=[validators.NumberRange(min=-90, max=90)])
    loc2_longitude = fields.FloatField(
        'Longitude of Location 2 (Dallas is -96.8)',
        validators=[validators.NumberRange(min=-180, max=180)])
    distance = fields.FloatField(
        'Distance within (KM)',
        validators=[validators.NumberRange(min=0)],
    )
    method = fields.SelectField('Visualization Method',
                                choices=[('bar', 'Bar'), ('pie', 'Pie')])
    submit = fields.SubmitField('Submit')

class StatForm2(FlaskForm):
    num_quake = fields.IntegerField(
        'Number of earthquakes:', validators=[validators.NumberRange(min=0, max=100000)])
    method = fields.SelectField('Visualization Method',
                                choices=[('scat','Scatter')])
    submit = fields.SubmitField('Submit')

# flask router

@app.route('/', methods=['GET', 'POST'])
def index():
    title = 'Upload Earthquake Dataset into Database'
    form = FileForm()
    if form.validate_on_submit():
        message = 'Upload Failed!'
        filename = secure_filename(form.file.data.filename)
        if helper.is_valid_ext(filename, app.config['allowed_csv_ext']):
            filename = os.path.join(app.config['csv_upload_dir'], filename)
            form.file.data.save(filename)
            helper.insert_csv_to_db(filename, EarthquakeDB, db)
            message = 'Upload Success!'
        return render_template('index.html',
                               title=title,
                               form=form,
                               message=message)
    return render_template('index.html', title=title, form=form)


@app.route('/stat', methods=['GET', 'POST'])
def stat():
    title = 'Data Visualization of Magnitude vs Depth in last N earthquakes'
    form = StatForm()
    if form.validate_on_submit():
        low = form.low.data
        high = form.high.data
        method = form.method.data
        label = []
        data = []
        for i in range(low, high):
            label.append(f'{i} - {i + 1}')
            result = EarthquakeDB.query.filter(
                (EarthquakeDB.mag >= i)
                & (EarthquakeDB.mag < i + 1)).all()
            data.append(len(result))
        viz = helper.get_viz(method, label, data)
        return render_template('queryChart.html',
                               title=title,
                               form=form,
                               viz=viz.render_embed(),
                               host=viz.js_host,
                               script_list=viz.js_dependencies.items)
    return render_template('queryChart.html', title=title, form=form)

@app.route('/stat-2', methods=['GET', 'POST'])
def stat2():
    title = 'Data Visualization of Magnitude'
    form = StatForm2()
    if form.validate_on_submit():
        num_quake = form.num_quake.data
        method = form.method.data
        label = []
        data = []
        result = EarthquakeDB.query.with_entities(EarthquakeDB.mag, EarthquakeDB.depth).order_by(EarthquakeDB.time.desc()).limit(num_quake).all()
        for item in result:
            data.append([item[0],item[1]])
        print('dsdsdsds')
        print(data)
        # breakpoint()
        viz = helper.get_viz(method, label, data)
        return render_template('queryChart.html',
                               title=title,
                               form=form,
                               viz=viz.render_embed(),
                               host=viz.js_host,
                               script_list=viz.js_dependencies.items)
    return render_template('queryChart.html', title=title, form=form)


@app.route('/compare', methods=['GET', 'POST'])
def compare():
    title = 'Data Visualization of Compare'
    form = CompareForm()
    if form.validate_on_submit():
        loc1_lat = form.loc1_latitude.data
        loc1_long = form.loc1_longitude.data
        loc2_lat = form.loc2_latitude.data
        loc2_long = form.loc2_longitude.data
        distance = form.distance.data
        method = form.method.data
        all_info = EarthquakeDB.query.all()
        loc1_count = 0
        loc2_count = 0
        for info in all_info:
            if helper.dist_from_loc(
                [loc1_lat, loc1_long],
                [info.latitude, info.longitude]) <= distance:
                loc1_count += 1
            if helper.dist_from_loc(
                [loc2_lat, loc2_long],
                [info.latitude, info.longitude]) <= distance:
                loc2_count += 1
        label = ['Location1', 'Location2']
        data = [loc1_count, loc2_count]
        viz = helper.get_viz(method, label, data)
        return render_template('queryChart.html',
                               title=title,
                               form=form,
                               viz=viz.render_embed(),
                               host=viz.js_host,
                               script_list=viz.js_dependencies.items)
    return render_template('queryChart.html', title=title, form=form)

@app.errorhandler(404)
@app.route('/404')
def page_not_found(error):
    return render_template('error404.html', title='404')


@app.errorhandler(500)
@app.route('/500')
def requests_error(error):
    return render_template('error500.html', title='500')


if __name__ == "__main__":
    helper.init_check(app.config['csv_upload_dir'])
    db.create_all()
    app.run(host=app.config['host'], port=app.config['port'])     