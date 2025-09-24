import os
import sys
import json

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ['FLASK_ENV'] = 'production'

from app import app, db
from data_models.content_models import Lesson, Reference


SECTION_HTML = '''<h3>Module 1 References</h3>
<p>Below are references and additional reading related to Module 1. Your instructor may update this list over time.</p>
<ul>
  <li><a href="#" target="_blank">(Placeholder) Add a reference link here</a></li>
  <li><a href="#" target="_blank">(Placeholder) Add a reference link here</a></li>
  <li><a href="#" target="_blank">(Placeholder) Add a reference link here</a></li>
</ul>
'''


DEFAULT_REFS = [
    (5, 'CISA: Understanding and Recognizing Phishing', 'https://www.cisa.gov/news-events/news/understanding-and-recognizing-phishing'),
    (6, 'NIST: Phishing Resources', 'https://www.nist.gov/itl/smallbusinesscyber/phishing'),
    (7, 'Microsoft: Social engineering red flags', 'https://www.microsoft.com/en/security/blog/2022/05/03/dont-fall-for-it-spotting-social-engineering-red-flags/'),
]


def main():
    with app.app_context():
        db.create_all()

        # Create a dedicated references lesson (order 15)
        ref_lesson = Lesson.query.filter_by(module_id=1, order=15).first()
        if not ref_lesson:
            ref_lesson = Lesson(
                module_id=1,
                order=15,
                title='Module 1 References',
                summary='Curated references and additional reading for Module 1.',
                content_rich=SECTION_HTML,
                video_url=None,
                video_type=None,
                attachment_urls=json.dumps([]),
                est_time_min=1,
            )
            db.session.add(ref_lesson)
        else:
            ref_lesson.title = 'Module 1 References'
            ref_lesson.summary = 'Curated references and additional reading for Module 1.'
            ref_lesson.content_rich = SECTION_HTML
            ref_lesson.video_url = None
            ref_lesson.video_type = None
            ref_lesson.attachment_urls = json.dumps([])
            ref_lesson.est_time_min = 1

        # Seed some default references if they don't exist yet
        for order, label, url in DEFAULT_REFS:
            existing = Reference.query.filter_by(module_id=1, order=order, label=label).first()
            if not existing:
                db.session.add(Reference(module_id=1, order=order, label=label, url=url))

        db.session.commit()
        print('OK: Module 1 References section created with placeholders and defaults')


if __name__ == '__main__':
    main()




