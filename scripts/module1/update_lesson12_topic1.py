import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(SCRIPTS_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ['FLASK_ENV'] = 'production'

from app import app, db
from data_models.content_models import Lesson, LessonTopic
from helper_utilities.video_map import get_video_id


CONTENT_HTML = (
    """
<p>Welcome to this lesson! You've already learned what social engineering is. Now, let’s go deeper. This video will show you why these attacks work so well by revealing the psychological triggers scammers use. Get ready to learn how to spot and resist the manipulators' tricks.</p>
"""
).strip()


def main():
    with app.app_context():
        db.create_all()
        # Lesson 1.2 uses order=12 per convention (11->1.1, 12->1.2)
        lesson = Lesson.query.filter_by(module_id=1, order=12).first()
        if not lesson:
            print('Lesson 1.2 not found')
            return

        # Ensure no lesson-level content duplicates topic rendering
        lesson.video_url = None
        lesson.content_rich = ''

        # Topic 1: The Psychology Behind the Deception (text then video)
        topic = LessonTopic.query.filter_by(lesson_id=lesson.id, order=1).first()
        if not topic:
            topic = LessonTopic(lesson_id=lesson.id, order=1, title='Lesson 1.2 The Psychology Behind the Deception')
            db.session.add(topic)
        topic.title = 'Lesson 1.2 The Psychology Behind the Deception'
        topic.content_rich = CONTENT_HTML
        yt_id = get_video_id('module1_lesson_1_2_a')
        topic.video_url = f'https://www.youtube-nocookie.com/embed/{yt_id}' if yt_id else None

        db.session.commit()
        print('OK: Lesson 1.2 topic 1 updated with intro text and Part A video')


if __name__ == '__main__':
    main()




