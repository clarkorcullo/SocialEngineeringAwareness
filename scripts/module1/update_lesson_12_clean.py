import os
import sys
import json

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ['FLASK_ENV'] = 'production'

from app import app, db
from data_models.content_models import Lesson


CLEAN_HTML = '''<h3>Lesson 1.2: The Psychology Behind the Deception</h3>
<p>Why social engineering works: urgency, authority, and cognitive biases. Watch the video, then review the key ideas below.</p>
<ul>
  <li><strong>Authority:</strong> We tend to trust messages that appear to come from people in charge.</li>
  <li><strong>Urgency:</strong> Fake deadlines push fast decisions without verification.</li>
  <li><strong>Cognitive biases:</strong> Mental shortcuts scammers exploit to influence choices.</li>
  <li><strong>Action:</strong> Pause, verify the sender, and inspect links before you act.</li>
</ul>
'''


def main():
    with app.app_context():
        db.create_all()
        lesson = Lesson.query.filter_by(module_id=1, order=12).first()
        if not lesson:
            print('Lesson 1.2 not found')
            return
        lesson.content_rich = CLEAN_HTML
        db.session.commit()
        print('OK: Lesson 1.2 content cleaned')


if __name__ == '__main__':
    main()




