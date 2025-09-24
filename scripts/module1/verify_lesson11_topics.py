import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ['FLASK_ENV'] = 'production'

from app import app, db
from data_models.content_models import Lesson, LessonTopic


def main():
    with app.app_context():
        lesson = Lesson.query.filter_by(module_id=1, order=11).first()
        if not lesson:
            print('Lesson 1.1 not found')
            return
        topics = LessonTopic.query.filter_by(lesson_id=lesson.id).order_by(LessonTopic.order).all()
        print(f"Lesson 1.1 ({lesson.id}) topics:")
        for t in topics:
            print(f"  order={t.order} title={t.title}")


if __name__ == '__main__':
    main()




