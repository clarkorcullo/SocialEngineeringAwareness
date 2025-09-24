import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ['FLASK_ENV'] = 'production'

from app import app, db
from data_models.content_models import Lesson, LessonTopic


CONTENT_HTML = (
    """
<p>Now, we're going to dive deeper into the mind of a social engineer and uncover the psychological principles they use to manipulate us. Understanding these tricks is your best defense!</p>
"""
).strip()


def main():
    with app.app_context():
        db.create_all()
        # Lesson 1.2 (order=12)
        lesson = Lesson.query.filter_by(module_id=1, order=12).first()
        if not lesson:
            print('Lesson 1.2 not found')
            return

        # Topic 2: The Manipulator's Toolkit
        topic = LessonTopic.query.filter_by(lesson_id=lesson.id, order=2).first()
        if not topic:
            topic = LessonTopic(lesson_id=lesson.id, order=2, title="The Manipulator's Toolkit")
            db.session.add(topic)
        topic.title = "The Manipulator's Toolkit"
        topic.content_rich = CONTENT_HTML
        # Use Part B video for this topic
        topic.video_url = '/static/animations/module1/Module 1 Lesson 1.2 Part B - The Psychology Behind the Deception.mov'

        db.session.commit()
        print("OK: Lesson 1.2 topic 2 updated with intro text and Part B video")


if __name__ == '__main__':
    main()




