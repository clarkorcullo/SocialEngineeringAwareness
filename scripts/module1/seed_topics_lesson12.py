import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ['FLASK_ENV'] = 'production'

from app import app, db
from data_models.content_models import Lesson, LessonTopic


def upsert_topic(lesson_id: int, order: int, title: str, content: str):
    topic = LessonTopic.query.filter_by(lesson_id=lesson_id, order=order).first()
    if not topic:
        topic = LessonTopic(lesson_id=lesson_id, order=order, title=title)
        db.session.add(topic)
    topic.title = title
    topic.content_rich = content
    return topic


def main():
    with app.app_context():
        db.create_all()
        lesson = Lesson.query.filter_by(module_id=1, order=12).first()
        if not lesson:
            print('Lesson 1.2 not found')
            return

        upsert_topic(lesson.id, 1, 'The Psychology Behind the Deception', '<p>(Details Content Here)</p>')
        upsert_topic(lesson.id, 2, "The Manipulator's Toolkit", '<p>(Details Content Here)</p>')
        upsert_topic(lesson.id, 3, 'Module 1 Conclusion: The Power of an Informed Mindset', '<p>(Details Content Here)</p>')
        db.session.commit()
        print('OK: Lesson 1.2 topics upserted')


if __name__ == '__main__':
    main()




