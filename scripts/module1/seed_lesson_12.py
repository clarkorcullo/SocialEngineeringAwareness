import os
import json
import sys

# Ensure project root is on sys.path for `import app`
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(SCRIPTS_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Ensure safe config selection (override any trailing-space value)
os.environ['FLASK_ENV'] = 'production'

from app import app, db
from data_models.content_models import Lesson
from helper_utilities.video_map import get_video_id


HTML = '''<h3>Lesson 1.2: The Psychology Behind the Deception</h3>
<p>Welcome to this lesson! You\'ve already learned what social engineering is. Now, let’s go deeper. This video will show you why these attacks work so well by revealing the psychological triggers scammers use. Get ready to learn how to spot and resist the manipulators\' tricks.</p>
<p><strong>Video Type:</strong> Animated Explainer (Duration: ~1:30)</p>
<hr/>
<h4>[0:00 - 0:15] The Hook</h4>
<p><em>Visuals:</em> An animated scene of a person shopping online. A pop-up appears on a travel site showing "Only 2 seats left at this price!" The person quickly clicks.</p>
<p><em>Narration:</em> Ever bought something just because the website said, \"Only two left at this price\"? You know that feeling—that instant pressure to act fast? That’s urgency, and it\'s just one of the powerful psychological tricks scammers use every day.</p>

<h4>[0:15 - 0:45] The Explanation</h4>
<p><em>Visuals:</em> The screen transitions to show a brain icon with gears. Text appears: "Mental Shortcuts" and "Cognitive Biases." A simple graphic of a person walking along a path with a fork in the road.</p>
<p><em>Narration:</em> Our brains love shortcuts. We’re overloaded with information, so we rely on quick judgments, or what psychologists call cognitive biases. The good news is, by understanding these mental shortcuts, you can turn them into a shield against scams.</p>

<h4>[0:45 - 1:15] The Example</h4>
<p><em>Visuals:</em> A professional-looking email with a fake logo appears. The email is signed by \"The Dean.\" An animated pop-up shows an urgent subject line.</p>
<p><em>Narration:</em> For example, a scammer might send you an email that looks like it\'s from your professor or a university official. They use the <strong>Principle of Authority</strong> to make you trust them. When they add a message like, \"Your account is about to be deactivated,\" they\'re using the <strong>Principle of Urgency</strong>. It\'s an emotional trigger that makes you bypass your common sense.</p>

<h4>[1:15 - 1:30] The Conclusion (Reassurance)</h4>
<p><em>Visuals:</em> A hand holding a magnifying glass appears over the email. A shield icon pops up. The text \"Smarter Than the Scam\" appears.</p>
<p><em>Narration:</em> This lesson is about knowing these tricks. By understanding how scammers try to influence your decisions, you’ll be much better at spotting their fake requests. It\'s about empowering you to be smarter than the scam.</p>
'''


def main():
    with app.app_context():
        db.create_all()
        lesson = Lesson.query.filter_by(module_id=1, order=12).first()
        yt_id = get_video_id('module1_lesson_1_2_a')
        video_path = f'https://www.youtube-nocookie.com/embed/{yt_id}' if yt_id else None
        if not lesson:
            lesson = Lesson(
                module_id=1,
                order=12,
                title='The Psychology Behind the Deception',
                summary='Why social engineering works: urgency, authority, and cognitive biases.',
                content_rich=HTML,
                video_url=video_path,
                video_type='animated',
                attachment_urls=json.dumps([]),
                est_time_min=2,
            )
            db.session.add(lesson)
        else:
            lesson.title = 'The Psychology Behind the Deception'
            lesson.summary = 'Why social engineering works: urgency, authority, and cognitive biases.'
            lesson.content_rich = HTML
            lesson.video_url = video_path
            lesson.video_type = 'animated'
            lesson.attachment_urls = json.dumps([])
            lesson.est_time_min = 2
        db.session.commit()
        print('OK: Lesson 1.2 saved')


if __name__ == '__main__':
    main()


