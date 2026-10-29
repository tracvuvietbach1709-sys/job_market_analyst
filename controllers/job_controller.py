from flask import Blueprint, jsonify, redirect, render_template, request, flash, url_for
from models.job_model import list_jobs, options, summary, insert_csv, ROLES, LEVELS

jobs = Blueprint('jobs', __name__)


def selected():
    return {key: request.args.get(key, '').strip() for key in ('role', 'level', 'city', 'source')}


@jobs.get('/')
def dashboard():
    filters = selected()
    return render_template('dashboard.html', data=summary(**filters), items=list_jobs(**filters, limit=100),
                           opts=options(), filters=filters)


@jobs.get('/api/summary')
def api_summary():
    return jsonify(summary(**selected()))


@jobs.get('/api/jobs')
def api_jobs():
    return jsonify(list_jobs(**selected(), limit=500))


@jobs.post('/upload')
def upload():
    file = request.files.get('file')
    if not file or not file.filename or not file.filename.lower().endswith('.csv'):
        flash('Vui lòng chọn tệp .csv hợp lệ.', 'error')
        return redirect(url_for('jobs.dashboard'))
    try:
        added, skipped = insert_csv(file.read(5 * 1024 * 1024 + 1))
        flash(f'Đã nhập {added} bản tin; bỏ qua {skipped} bản tin trùng.', 'success')
    except ValueError as exc:
        flash(str(exc), 'error')
    return redirect(url_for('jobs.dashboard'))
