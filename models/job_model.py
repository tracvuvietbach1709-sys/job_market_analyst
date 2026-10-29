import csv
import hashlib
import io
import json
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / 'data' / 'jobs.db'
ROLES = ('Data Analyst', 'IT Risk', 'Business Analyst', 'Software Development', 'Cyber Security')
LEVELS = ('Intern', 'Fresher', 'Junior', 'Senior')


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    with connect() as con:
        con.execute('''CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            external_id TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            role TEXT NOT NULL,
            level TEXT NOT NULL,
            city TEXT NOT NULL,
            salary_min REAL,
            salary_max REAL,
            skills TEXT NOT NULL,
            company TEXT NOT NULL,
            source TEXT NOT NULL,
            source_url TEXT NOT NULL DEFAULT '',
            posted_date TEXT NOT NULL
        )''')
        con.execute('CREATE INDEX IF NOT EXISTS idx_jobs_role ON jobs(role)')
        con.execute('CREATE INDEX IF NOT EXISTS idx_jobs_city ON jobs(city)')


def split_skills(raw):
    if not raw:
        return []
    values = raw if isinstance(raw, list) else str(raw).replace('|', ';').split(';')
    seen = set()
    result = []
    aliases = {'power bi': 'Power BI', 'sql': 'SQL', 'python': 'Python', 'excel': 'Excel',
               'tableau': 'Tableau', 'etl': 'ETL', 'jira': 'Jira', 'aws': 'AWS',
               'risk assessment': 'Risk Assessment', 'data visualization': 'Data Visualization',
               'business analysis': 'Business Analysis', 'requirements gathering': 'Requirements Gathering',
               'stakeholder management': 'Stakeholder Management', 'iso 27001': 'ISO 27001',
               'information security': 'Information Security', 'agile': 'Agile', 'scrum': 'Scrum',
               'statistics': 'Statistics', 'data modeling': 'Data Modeling', 'process mapping': 'Process Mapping',
               'internal audit': 'Internal Audit', 'cobit': 'COBIT', 'it governance': 'IT Governance',
               'communication': 'Communication', 'r': 'R', 'javascript': 'JavaScript', 'typescript': 'TypeScript', 'git': 'Git', 'docker': 'Docker', 'react': 'React', 'java': 'Java', 'linux': 'Linux', 'network security': 'Network Security', 'siem': 'SIEM', 'incident response': 'Incident Response', 'penetration testing': 'Penetration Testing', 'owasp': 'OWASP', 'vulnerability assessment': 'Vulnerability Assessment', 'soc': 'SOC'}
    for v in values:
        v = str(v).strip()
        if not v:
            continue
        canonical = aliases.get(v.lower(), v)
        if canonical.casefold() not in seen:
            result.append(canonical)
            seen.add(canonical.casefold())
    return result


def _filters(role='', level='', city='', source=''):
    clauses, args = [], []
    for col, value, allowed in [('role', role, ROLES), ('level', level, LEVELS), ('city', city, None), ('source', source, None)]:
        if value and (allowed is None or value in allowed):
            clauses.append(f'{col} = ?')
            args.append(value)
    return (' WHERE ' + ' AND '.join(clauses)) if clauses else '', args


def list_jobs(role='', level='', city='', source='', limit=100):
    where, args = _filters(role, level, city, source)
    with connect() as con:
        rows = con.execute('SELECT * FROM jobs' + where + ' ORDER BY posted_date DESC, id DESC LIMIT ?', (*args, limit)).fetchall()
    return [{**dict(row), 'skills': json.loads(row['skills'])} for row in rows]


def options():
    with connect() as con:
        cities = [r[0] for r in con.execute('SELECT DISTINCT city FROM jobs ORDER BY city')]
        sources = [r[0] for r in con.execute('SELECT DISTINCT source FROM jobs ORDER BY source')]
    return {'roles': ROLES, 'levels': LEVELS, 'cities': cities, 'sources': sources}


def summary(role='', level='', city='', source=''):
    where, args = _filters(role, level, city, source)
    with connect() as con:
        rows = con.execute('SELECT role, level, city, salary_min, salary_max, skills FROM jobs' + where, args).fetchall()
    counts = Counter()
    cities = Counter()
    roles = Counter()
    salaries = defaultdict(list)
    published_salary = 0
    for row in rows:
        roles[row['role']] += 1
        cities[row['city']] += 1
        counts.update(json.loads(row['skills']))  # 1 job = 1 demand per skill
        lo, hi = row['salary_min'], row['salary_max']
        if lo is not None or hi is not None:
            published_salary += 1
            salaries[row['level']].append((lo + hi) / 2 if lo is not None and hi is not None else (lo if lo is not None else hi))
    salary_means = {lvl: round(sum(salaries[lvl]) / len(salaries[lvl]), 2) if salaries[lvl] else None for lvl in LEVELS}
    return {
        'total': len(rows), 'salary_sample': published_salary, 'top_skills': [{'name': k, 'count': v} for k, v in counts.most_common(5)],
        'cities': [{'name': k, 'count': v} for k, v in cities.most_common()],
        'roles': [{'name': k, 'count': roles.get(k, 0)} for k in ROLES],
        'salary_by_level': [{'level': lvl, 'average': salary_means[lvl], 'count': len(salaries[lvl])} for lvl in LEVELS],
        'salary_unit': 'triệu VND/tháng',
    }


def _salary(value):
    text = str(value or '').strip().replace(',', '.')
    if not text or text.lower() in ('none', 'n/a', 'negotiable', 'thỏa thuận'):
        return None
    number = float(text)
    if number < 0 or number > 1000:
        raise ValueError('Mức lương phải từ 0 đến 1,000 triệu VND/tháng')
    return number


def insert_csv(content):
    if len(content) > 5 * 1024 * 1024:
        raise ValueError('CSV vượt quá giới hạn 5 MB')
    try:
        decoded = content.decode('utf-8-sig')
    except UnicodeDecodeError:
        raise ValueError('CSV cần sử dụng mã hóa UTF-8')
    reader = csv.DictReader(io.StringIO(decoded))
    required = {'title', 'role', 'level', 'city', 'salary_min', 'salary_max', 'skills', 'company', 'source', 'posted_date'}
    if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
        raise ValueError('Thiếu cột CSV bắt buộc: ' + ', '.join(sorted(required - set(reader.fieldnames or []))))
    added, skipped = 0, 0
    with connect() as con:
        for line, row in enumerate(reader, 2):
            if line > 10002:
                raise ValueError('Tối đa 10,000 dòng mỗi lần tải lên')
            try:
                role = str(row['role'] or '').strip()
                level = str(row['level'] or '').strip()
                if role not in ROLES or level not in LEVELS:
                    raise ValueError('role hoặc level không hợp lệ')
                title, city, company, source = [str(row[k] or '').strip() for k in ('title', 'city', 'company', 'source')]
                if not all((title, city, company, source)):
                    raise ValueError('Thiếu title, city, company hoặc source')
                date = datetime.strptime(str(row['posted_date'] or ''), '%Y-%m-%d').date().isoformat()
                lo, hi = _salary(row['salary_min']), _salary(row['salary_max'])
                if lo is not None and hi is not None and lo > hi:
                    raise ValueError('salary_min lớn hơn salary_max')
                skills = split_skills(row['skills'])
                url = str(row.get('source_url') or '').strip()
                if url and not url.startswith(('https://', 'http://')):
                    raise ValueError('source_url phải là http(s)')
                external_id = str(row.get('external_id') or '').strip()
                if not external_id:
                    fingerprint = '|'.join((title, role, level, city, company, source, date, url))
                    external_id = hashlib.sha256(fingerprint.encode()).hexdigest()
                before = con.total_changes
                con.execute('''INSERT OR IGNORE INTO jobs
                   (external_id, title, role, level, city, salary_min, salary_max, skills, company, source, source_url, posted_date)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (external_id, title, role, level, city, lo, hi, json.dumps(skills, ensure_ascii=False), company, source, url, date))
                if con.total_changes > before:
                    added += 1
                else:
                    skipped += 1
            except (ValueError, TypeError, OverflowError) as exc:
                raise ValueError(f'Dòng {line}: {exc}') from exc
    return added, skipped
