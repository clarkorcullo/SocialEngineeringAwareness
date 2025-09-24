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
        db.create_all()

        # Remove empty topic folders for Lesson 1.2 (order=12)
        lesson = Lesson.query.filter_by(module_id=1, order=12).first()
        if lesson:
            topics = LessonTopic.query.filter_by(lesson_id=lesson.id).order_by(LessonTopic.order).all()
            removed = []
            for t in topics:
                # Remove topics with no content and no video
                if (not t.content_rich or t.content_rich.strip() == '') and (not t.video_url or t.video_url.strip() == ''):
                    removed.append(t.title)
                    db.session.delete(t)

            db.session.commit()
            print('Removed empty topics:', removed)

        # Remove stray Lessons that should not be standalone cards
        stray_titles = [
            'Module 1 References',
            "The Manipulator's Toolkit",
            'Module 1 Conclusion: The Power of an Informed Mindset',
        ]
        removed_lessons = []
        for t in stray_titles:
            stray = Lesson.query.filter_by(module_id=1, title=t).first()
            if stray:
                db.session.delete(stray)
                removed_lessons.append(t)
        if removed_lessons:
            db.session.commit()
            print('Removed stray lessons:', removed_lessons)

        print('Cleanup complete')


if __name__ == '__main__':
    main()


