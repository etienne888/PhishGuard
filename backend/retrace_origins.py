"""
Re-trace the sender origin of stored e-mail analyses from their saved hops.

Needed once after the fix that stopped treating every e-mail delivered to a Gmail /
Outlook inbox as "hidden by provider". No raw e-mail is required: the Received hops
are already stored in analyses.indicators['origin'].

Usage:  python retrace_origins.py            (dry run: counts only)
        python retrace_origins.py --apply
"""
import json
import os
import sys
from collections import Counter

os.environ.setdefault('SCHEDULER_ENABLED', 'false')

from app import create_app, db  # noqa: E402
from app.models import Analysis  # noqa: E402
from app.services.email_origin import retrace  # noqa: E402


def main(apply: bool) -> None:
    app = create_app()
    with app.app_context():
        before, after = Counter(), Counter()
        for a in Analysis.query.filter(Analysis.source.in_(('mailbox', 'forward', 'web'))).all():
            raw = a.indicators
            try:
                data = json.loads(raw) if isinstance(raw, str) else raw
            except ValueError:
                continue
            if not isinstance(data, dict):  # legacy analyses stored a plain list of indicators
                continue
            data = dict(data)
            origin = data.get('origin')
            if not isinstance(origin, dict) or not origin.get('hops'):
                continue
            before[origin.get('precision')] += 1
            new = retrace(origin, instance_path=app.instance_path)
            after[new.get('precision')] += 1
            if apply:
                data['origin'] = new
                a.indicators = json.dumps(data)
        if apply:
            db.session.commit()
        print('before:', dict(before))
        print('after: ', dict(after), '(saved)' if apply else '(dry run, use --apply to save)')


if __name__ == '__main__':
    main('--apply' in sys.argv)
