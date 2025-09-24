import os
import sys
import json

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(SCRIPTS_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ['FLASK_ENV'] = 'production'

from app import app, db
from data_models.content_models import Lesson
from helper_utilities.video_map import get_video_id


MODULE1_DIR = os.path.join(PROJECT_ROOT, 'static', 'animations', 'module1')


def main():
    with app.app_context():
        db.create_all()

        # Use YouTube IDs via central map
        def yt_embed(video_key: str) -> str | None:
            vid = get_video_id(video_key)
            return f"https://www.youtube-nocookie.com/embed/{vid}" if vid else None

        v11 = yt_embed('module1_lesson_1_1_a')
        v12a = yt_embed('module1_lesson_1_2_a')
        v12b = yt_embed('module1_lesson_1_2_b')
        info_img = None  # optional: keep attachments empty to avoid static deps

        # Order 11: Lesson 1.1
        l11 = Lesson.query.filter_by(module_id=1, order=11).first()
        if l11 and v11:
            l11.video_url = v11
            l11.video_type = 'animated'
            # keep attachments unchanged

        # Order 12: Lesson 1.2 (Psychology - main)
        l12 = Lesson.query.filter_by(module_id=1, order=12).first()
        if l12:
            if v12a:
                l12.video_url = v12a
                l12.video_type = 'animated'
            # clear attachments that referenced local static files
            l12.attachment_urls = json.dumps([])

        # Order 13: Lesson 1.3 (Manipulator's Toolkit) — use Part B if present
        l13 = Lesson.query.filter_by(module_id=1, order=13).first()
        if l13 and v12b:
            l13.video_url = v12b
            l13.video_type = 'animated'

        db.session.commit()
        print('OK: Linked Module 1 videos to lessons')


if __name__ == '__main__':
    main()




