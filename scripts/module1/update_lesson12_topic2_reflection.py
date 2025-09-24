import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ['FLASK_ENV'] = 'production'

from app import app, db
from data_models.content_models import Lesson, LessonTopic, Reflection


CONTENT_HTML = (
    """
<h4>Reflection</h4>
<p>Think about a time when someone tried to get you to act quickly, trust them blindly, or give out personal information—online or offline.</p>
<ul>
  <li>What happened?</li>
  <li>Did you realize it might have been social engineering?</li>
  <li>How did you respond, and would you act differently now that you’ve completed this module?</li>
</ul>
<h5>Bonus</h5>
<p>Share one “aha moment” from this module. What surprised you, and what habit or mindset will you change starting today?</p>
"""
).strip()


def main():
    with app.app_context():
        db.create_all()
        lesson = Lesson.query.filter_by(module_id=1, order=12).first()
        if not lesson:
            print('Lesson 1.2 not found')
            return

        # Upsert Topic 2 as "The Manipulator's Toolkit" (Reflection content under this folder)
        topic = LessonTopic.query.filter_by(lesson_id=lesson.id, order=2).first()
        if not topic:
            topic = LessonTopic(lesson_id=lesson.id, order=2, title="The Manipulator's Toolkit")
            db.session.add(topic)
        topic.title = "The Manipulator's Toolkit"
        topic.content_rich = CONTENT_HTML
        topic.video_url = None

        # Remove module-level Reflection to avoid duplicate section at bottom
        existing_reflection = Reflection.query.filter_by(module_id=1).first()
        if existing_reflection:
            db.session.delete(existing_reflection)

        db.session.commit()
        print("OK: Lesson 1.2 topic 2 set to 'The Manipulator's Toolkit' with Reflection content; module Reflection removed")


if __name__ == '__main__':
    main()


