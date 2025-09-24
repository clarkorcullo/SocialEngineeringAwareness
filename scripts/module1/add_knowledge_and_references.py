import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ['FLASK_ENV'] = 'production'

from app import app, db
from data_models.content_models import Lesson


KNOWLEDGE_CHECK_HTML = (
    """
<h4>Knowledge Check</h4>
<p>Test your understanding of Module 1. You can retake as many times as you like. Passing score is 80%.</p>
<a href="/assessment/1" class="btn btn-warning">
  <i class="fas fa-question-circle me-2"></i>Start Knowledge Check
</a>
"""
).strip()


REFERENCES_HTML = (
    """
<h4>References</h4>
<ul>
  <li><a href="https://www.bbc.com/news/technology-53425822" target="_blank" rel="noopener">BBC: Major US Twitter accounts hacked in Bitcoin scam</a></li>
  <li><a href="https://www.ibm.com/topics/social-engineering" target="_blank" rel="noopener">IBM: What is Social Engineering?</a></li>
  <li><a href="https://people-shift.com/articles/cialdinis-6-principles-of-persuasion/" target="_blank" rel="noopener">Cialdini’s 6 Principles of Persuasion</a></li>
</ul>
"""
).strip()


def upsert_lesson(module_id: int, order: int, title: str, html: str):
    lesson = Lesson.query.filter_by(module_id=module_id, order=order).first()
    if not lesson:
        lesson = Lesson(module_id=module_id, order=order, title=title)
        db.session.add(lesson)
    lesson.title = title
    lesson.summary = None
    lesson.content_rich = html
    lesson.video_url = None
    lesson.video_type = None
    return lesson


def main():
    with app.app_context():
        db.create_all()

        # After Reflection (order=15), add Knowledge Check (16) and References (17)
        upsert_lesson(1, 16, 'Knowledge Check', KNOWLEDGE_CHECK_HTML)
        upsert_lesson(1, 17, 'References', REFERENCES_HTML)
        db.session.commit()
        print('OK: Added/updated Module 1 lessons for Knowledge Check (16) and References (17)')


if __name__ == '__main__':
    main()


