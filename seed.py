"""Tạo dữ liệu tổng hợp GIẢ LẬP, không phải dữ liệu LinkedIn/VietnamWorks thực tế."""
import csv
import random
from datetime import date, timedelta
from pathlib import Path
from models.job_model import init_db, insert_csv

ROLE_SKILLS = {
    'Data Analyst': ['SQL', 'Excel', 'Python', 'Power BI', 'Statistics', 'Tableau', 'Data Visualization', 'ETL', 'Data Modeling', 'Communication'],
    'IT Risk': ['Risk Assessment', 'ISO 27001', 'Information Security', 'COBIT', 'IT Governance', 'Internal Audit', 'Excel', 'SQL', 'Communication', 'AWS'],
    'Business Analyst': ['Requirements Gathering', 'Jira', 'Agile', 'Business Analysis', 'SQL', 'Process Mapping', 'Stakeholder Management', 'Scrum', 'Excel', 'Communication'],
    'Software Development': ['Python', 'Java', 'JavaScript', 'TypeScript', 'Git', 'React', 'Docker', 'SQL', 'Agile', 'AWS'],
    'Cyber Security': ['Network Security', 'Linux', 'SIEM', 'Incident Response', 'ISO 27001', 'Penetration Testing', 'OWASP', 'Vulnerability Assessment', 'Python', 'SOC'],
}
SALARIES = {'Intern': (3, 7), 'Fresher': (7, 12), 'Junior': (14, 26), 'Senior': (30, 58)}
CITIES = ['TP. Hồ Chí Minh', 'Hà Nội', 'Đà Nẵng', 'Bình Dương', 'Cần Thơ']
SOURCES = ['LinkedIn', 'VietnamWorks']


def make_sample(path, count=200):
    rand = random.Random(42)
    cols = ['external_id', 'title', 'role', 'level', 'city', 'salary_min', 'salary_max', 'skills', 'company', 'source', 'source_url', 'posted_date']
    path = Path(path)
    with path.open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        for i in range(count):
            role = rand.choice(list(ROLE_SKILLS))
            level = rand.choices(['Intern', 'Fresher', 'Junior', 'Senior'], weights=[15, 25, 38, 22])[0]
            city = rand.choices(CITIES, weights=[48, 33, 12, 5, 2])[0]
            base_min, base_max = SALARIES[level]
            has_salary = rand.random() > .22
            salary_min = round(base_min + rand.uniform(-1, 3), 1) if has_salary else ''
            salary_max = round(max(float(salary_min), base_max + rand.uniform(-2, 4)), 1) if has_salary else ''
            skills = rand.sample(ROLE_SKILLS[role][:6], 3) + rand.sample(ROLE_SKILLS[role][6:], 2)
            writer.writerow({
                'external_id': f'DEMO-{i+1:04}', 'title': f'{level} {role}', 'role': role, 'level': level,
                'city': city, 'salary_min': salary_min, 'salary_max': salary_max,
                'skills': ';'.join(skills), 'company': f'Demo Company {i%18+1:02}',
                'source': SOURCES[i % 2], 'source_url': '',
                'posted_date': (date(2026, 10, 28) - timedelta(days=rand.randint(0, 90))).isoformat(),
            })
    return path


if __name__ == '__main__':
    init_db()
    path = make_sample(Path(__file__).parent / 'static' / 'sample_jobs.csv')
    added, skipped = insert_csv(path.read_bytes())
    print(f'Đã nạp {added} tin minh họa, bỏ qua {skipped} trùng lặp.')
