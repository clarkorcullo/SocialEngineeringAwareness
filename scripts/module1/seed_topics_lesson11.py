import os
import sys
import json

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ['FLASK_ENV'] = 'production'

from app import app, db
from data_models.content_models import Lesson, LessonTopic


def upsert_topic(lesson_id: int, order: int, title: str, content: str, video_url: str | None = None):
    topic = LessonTopic.query.filter_by(lesson_id=lesson_id, order=order).first()
    if not topic:
        topic = LessonTopic(lesson_id=lesson_id, order=order, title=title)
        db.session.add(topic)
    topic.title = title
    topic.content_rich = content
    topic.video_url = video_url
    return topic


def main():
    with app.app_context():
        db.create_all()
        lesson = Lesson.query.filter_by(module_id=1, order=11).first()
        if not lesson:
            print('Lesson 1.1 not found. Seed lesson first.')
            return

        upsert_topic(lesson.id, 1, 'What is Social Engineering?', '<p>Definition and why it matters.</p>')
        upsert_topic(lesson.id, 2, 'The Anatomy of a Human-Based Attack', '<p>Core tactics: urgency, authority, liking.</p>')
        upsert_topic(lesson.id, 3, 'Conclusion & Resources', '<p>Keep a skeptical mindset. See references below.</p>')
        db.session.commit()
        print('OK: Lesson 1.1 topics upserted')


if __name__ == '__main__':
    main()




