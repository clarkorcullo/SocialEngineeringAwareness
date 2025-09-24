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


HTML = '''<h3>Lesson 1.1: What is Social Engineering?</h3>
<p>Welcome to our first lesson! We’re starting with a simple but crucial concept: social engineering. It’s the most common and dangerous cyber threat you’ll face today. It doesn’t rely on complex code or sophisticated technology; it relies on human psychology.</p>
<p>This short video will give you a quick overview of what social engineering is and why it’s so effective. After watching, you’ll have a clear understanding of what “human hacking” is all about.</p>
<hr/>
<h4>Core Lesson Content: The Anatomy of a Human-Based Attack</h4>
<p>Social engineering attacks manipulate people into sharing information, downloading software, or making other mistakes that compromise their security. It’s sometimes called “human hacking,” because it uses psychological manipulation instead of technical skills. Even with strong firewalls and antivirus, a crafty attacker targets the user.</p>
<ul>
  <li><strong>Urgency:</strong> “Your account will be suspended in 5 minutes!”</li>
  <li><strong>Authority:</strong> Impersonating IT, registrar, or government</li>
  <li><strong>Liking/Trust:</strong> Pretending to be a friend or classmate</li>
</ul>
<h5>Social Engineering in a Nutshell</h5>
<p>Use the infographic as a quick reference for psychological tricks to help you spot scams fast.</p>
'''


def main():
    module_id = 1
    video = '/static/animations/module1/Module 1 Lesson 1.1 Part A - What is Social Engineering_.mov'
    infographic = '/static/animations/module1/Blue and White Illustrated Tips  Successful Business Infographic Poster (8).png '
    with app.app_context():
        db.create_all()
        lesson = Lesson.query.filter_by(module_id=module_id, order=11).first()
        if not lesson:
            lesson = Lesson(
                module_id=module_id,
                order=11,
                title='What is Social Engineering?',
                summary='Intro to social engineering and why it works (human hacking).',
                content_rich=HTML,
                video_url=video,
                video_type='animated',
                attachment_urls=json.dumps([infographic]),
                est_time_min=3,
            )
            db.session.add(lesson)
        else:
            lesson.title = 'What is Social Engineering?'
            lesson.summary = 'Intro to social engineering and why it works (human hacking).'
            lesson.content_rich = HTML
            lesson.video_url = video
            lesson.video_type = 'animated'
            lesson.attachment_urls = json.dumps([infographic])
            lesson.est_time_min = 3
        db.session.commit()
        print('OK: Lesson 1.1 upserted')


if __name__ == '__main__':
    main()




