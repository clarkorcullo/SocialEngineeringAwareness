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
<h4>Core Lesson Content: The Anatomy of a Human-Based Attack</h4>
<p>Social engineering attacks manipulate people into sharing information, downloading software, or making other mistakes that compromise their security. It’s sometimes called “human hacking,” because it uses psychological manipulation instead of technical skills. According to reports, social engineering is a leading cause of network compromise today.</p>
<p>This is one of the biggest challenges in cybersecurity. Even with strong firewalls and up-to-date antivirus software, a crafty social engineer can get right through by targeting you, the user. It’s like having a strong lock on your door, but a scammer just convinces you to hand them the key.</p>
<p>So, how does it work? Social engineering is a game of psychology. Attackers use one or more of these principles to trick you into acting against your own best interest:</p>
<ul>
  <li><strong>Urgency:</strong> Scammers create a sense of panic to make you act rashly. They might say, “Your account will be suspended in 5 minutes!”</li>
  <li><strong>Authority:</strong> Attackers impersonate a person in power (e.g., IT, registrar, government) to make requests seem legitimate and non‑negotiable.</li>
  <li><strong>Liking/Trust:</strong> They appeal to your better nature or a personal connection to lower your guard.</li>
  <li><strong>Understanding these tricks is your best defense.</strong> By recognizing the psychology behind the deception, you can stay safe online.</li>
 </ul>
<div class="mt-3">
  <h5>Social Engineering in a Nutshell</h5>
  <p>Use this quick reference to remember the psychological levers attackers use.</p>
  <img class="img-fluid rounded border" alt="Social Engineering in a Nutshell" src="/static/animations/module1/Blue%20and%20White%20Illustrated%20Tips%20%20Successful%20Business%20Infographic%20Poster%20(8).png" />
 </div>
"""
).strip()


def main():
    with app.app_context():
        db.create_all()
        lesson = Lesson.query.filter_by(module_id=1, order=11).first()
        if not lesson:
            print('Lesson 1.1 not found')
            return

        topic = LessonTopic.query.filter_by(lesson_id=lesson.id, order=2).first()
        if not topic:
            topic = LessonTopic(lesson_id=lesson.id, order=2, title='Core Lesson Content: The Anatomy of a Human-Based Attack')
            db.session.add(topic)
        topic.title = 'Core Lesson Content: The Anatomy of a Human-Based Attack'
        topic.content_rich = CONTENT_HTML
        topic.video_url = None

        db.session.commit()
        print('OK: Lesson 1.1 topic 2 updated')


if __name__ == '__main__':
    main()


