import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ['FLASK_ENV'] = 'production'

from app import app, db
from data_models.content_models import Lesson


def set_title(module_id: int, order: int, title: str):
    lesson = Lesson.query.filter_by(module_id=module_id, order=order).first()
    if not lesson:
        return False
    lesson.title = title
    return True


def main():
    with app.app_context():
        updated = []
        if set_title(1, 11, 'Lesson 1.1: What is Social Engineering?'):
            updated.append('1.1')
        if set_title(1, 12, 'Lesson 1.2: The Psychology Behind the Deception'):
            updated.append('1.2')
        db.session.commit()
        print('OK: Updated lesson titles ->', ', '.join(updated))


if __name__ == '__main__':
    main()




