"""
Apply one SQL script from database/scripts to the configured database.

    python apply_sql.py database/scripts/07_review_queue.sql
"""

import sys

from sqlalchemy import text

from app import create_app, db


def statements(sql: str):
    for chunk in sql.split(';'):
        body = '\n'.join(line for line in chunk.splitlines() if not line.strip().startswith('--')).strip()
        if body:
            yield body


def main(path: str):
    app = create_app()
    with app.app_context():
        with open(path, encoding='utf-8') as fh:
            for stmt in statements(fh.read()):
                db.session.execute(text(stmt))
        db.session.commit()
        print(f'Applied {path}')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
