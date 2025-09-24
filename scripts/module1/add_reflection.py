import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ['FLASK_ENV'] = 'production'

from app import app, db
from data_models.content_models import Lesson


CONTENT_HTML = (
    """
<h4>Module 1 Reflection: "Could This Happen to Me?"</h4>
<p>Welcome to your first reflection! Now that you’ve completed Module 1, it’s time to think about how social engineering shows up in your own life. This isn't just theory; it’s about making sure you’re ready to protect yourself. Take a few minutes to think about the questions below and share your thoughts.</p>
<h5>Reflection Prompts</h5>
<ul>
  <li>Think about a time when someone tried to get you to act quickly, trust them blindly, or give out personal information—online or offline. What happened?</li>
  <li>Now that you’ve completed this module, do you think it might have been a social engineering attempt?</li>
  <li>How did you respond then, and how would you act differently now?</li>
</ul>
<h5>Bonus</h5>
<p>Share one "aha moment" from this module. What surprised you the most about social engineering, and what habit or mindset will you change starting today?</p>
"""
).strip()


def main():
    with app.app_context():
        db.create_all()

        # Place Reflection after Lesson 1.2. Conventionally 11 -> 1.1, 12 -> 1.2, so use 15
        lesson = Lesson.query.filter_by(module_id=1, order=15).first()
        if not lesson:
            lesson = Lesson(module_id=1, order=15, title='Reflection')
            db.session.add(lesson)

        lesson.title = 'Reflection'
        lesson.summary = 'Module 1 Reflection: Could This Happen to Me?'
        lesson.content_rich = CONTENT_HTML
        lesson.video_url = None
        lesson.video_type = None

        db.session.commit()
        print('OK: Added/updated Module 1 lesson (order=15) as Reflection')


if __name__ == '__main__':
    main()




