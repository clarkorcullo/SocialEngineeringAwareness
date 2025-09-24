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
<p>Welcome to our first lesson! We're starting with a simple but crucial concept: social engineering. It's the most common and dangerous cyber threat you'll face today. It doesn't rely on complex code or sophisticated technology; it relies on human psychology.</p>
<p>This short video will give you a quick overview of what social engineering is and why it's so effective. After watching, you'll have a clear understanding of what "human hacking" is all about.</p>
"""
).strip()


def main():
    with app.app_context():
        db.create_all()
        lesson = Lesson.query.filter_by(module_id=1, order=11).first()
        if not lesson:
            print('Lesson 1.1 not found')
            return
        # Ensure lesson metadata is clean; render content only inside the topic (text first, then video)
        correct_video = '/static/animations/module1/Module 1 Lesson 1.1 Part A - What is Social Engineering_.mov'
        lesson.video_url = None
        lesson.content_rich = ''

        # Topic 1: Intro to Social Engineering and why it works (Human Hacking)
        topic = LessonTopic.query.filter_by(lesson_id=lesson.id, order=1).first()
        if not topic:
            topic = LessonTopic(lesson_id=lesson.id, order=1, title='Lesson 1.1 Intro to Social Engineering and why it works (Human Hacking)')
            db.session.add(topic)
        topic.title = 'Lesson 1.1 Intro to Social Engineering and why it works (Human Hacking)'
        topic.content_rich = CONTENT_HTML
        topic.video_url = correct_video

        db.session.commit()
        print('OK: Lesson 1.1 topic 1 updated with clean content and correct video')


if __name__ == '__main__':
    main()


