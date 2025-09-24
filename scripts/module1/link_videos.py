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


MODULE1_DIR = os.path.join(PROJECT_ROOT, 'static', 'animations', 'module1')


def main():
    with app.app_context():
        db.create_all()

        # Map by convention
        part_11 = 'Module 1 Lesson 1.1 Part A - What is Social Engineering_.mov'
        part_12a = 'Module 1 Lesson 1.2 Part A - The Psychology Behind the Deception.mov'
        part_12b = 'Module 1 Lesson 1.2 Part B - The Psychology Behind the Deception.mov'
        infographic = 'Blue and White Illustrated Tips  Successful Business Infographic Poster (8).png '

        # Helper to build /static path if file exists
        def static_path(filename: str):
            path = os.path.join(MODULE1_DIR, filename)
            return f"/static/animations/module1/{filename}" if os.path.exists(path) else None

        v11 = static_path(part_11)
        v12a = static_path(part_12a)
        v12b = static_path(part_12b)
        info_img = static_path(infographic)

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
            attachments = []
            if v12b:
                attachments.append(v12b)
            if info_img:
                attachments.append(info_img)
            if attachments:
                l12.attachment_urls = json.dumps(attachments)

        # Order 13: Lesson 1.3 (Manipulator's Toolkit) — use Part B if present
        l13 = Lesson.query.filter_by(module_id=1, order=13).first()
        if l13 and v12b:
            l13.video_url = v12b
            l13.video_type = 'animated'

        db.session.commit()
        print('OK: Linked Module 1 videos to lessons')


if __name__ == '__main__':
    main()




