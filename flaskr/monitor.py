#!/usr/bin/python3

import sys
sys.path.extend(('lib', 'db'))

from kleros import db, Dispute, Round, Vote, Config, Court, Juror
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///kleros.db'
db = SQLAlchemy(app)
config = Config()

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)

@app.route('/court/<int:id>', methods=['GET'])
def court(id):
    court = Court.query.get(id)
    disputes = Dispute.query.filter(Dispute.subcourt_id == id).order_by(Dispute.id.desc())
    jurors = court.jurors()
    jurors_stats = court.juror_stats()

    return render_template('monitor/court.html', court=court, disputes=disputes, jurors=jurors, last_updated=config.get('updated'), jurors_stats=jurors_stats)

@app.route('/', methods=['GET'])
@app.route('/disputes', methods=['GET'])
def disputes():
    disputes = Dispute.query.order_by(Dispute.id.desc()).all()
    for dispute in disputes:
        court = Court.query.get(dispute.subcourt_id)
        if court != None:
            dispute.court_name = court.name
        else:
            dispute.court_name = "Court #%" % dispute.subcourt_id

    return render_template('monitor/disputes.html', disputes=disputes, last_updated=config.get('updated'))

@app.route('/dispute/<int:id>', methods=['GET'])
def dispute(id):
    dispute = Dispute.query.get(id)
    rounds = Round.query.filter_by(dispute_id = id).all()
    votes = []
    for r in rounds:
        r.majority_reached = r.majority_reached()
        r.votes = Vote.query.filter_by(round_id = r.id).all()
        for v in r.votes:
            if v.choice == 1: v.vote_str = 'Yes'
            elif v.choice == 2: v.vote_str = 'No'
            else: v.vote_str = 'Pending'

            if r.majority_reached:
                if v.choice == 0: v.color = '#F7DC6F'
                elif v.choice == r.winning_choice(): v.color = '#27AE60'
                else: v.color = '#E74C3C'
            else:
                if v.choice == 0: v.color = '#FCF3CF'
                elif v.choice == r.winning_choice(): v.color = '#D1F2EB'
                else: v.color = '#F5B7B1'

    x = len(rounds)
    return render_template('monitor/dispute.html', dispute=dispute, rounds=rounds, x=x, last_updated=config.get('updated'))

@app.route('/juror/<string:address>', methods=['GET'])
def juror(address):
    juror = Juror.query.filter_by(address=address).first()
    stakings = juror.stakings()

    return render_template('monitor/juror.html', juror=juror, stakings = juror.stakings, last_updated=config.get('updated'))
