import os
import sys
import json

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ['FLASK_ENV'] = 'production'

from app import app, db
from data_models.content_models import Lesson, Reference, Reflection


LESSON_HTML = '''<h3>Module 1 Conclusion: The Power of an Informed Mindset</h3>
<p>Congratulations on completing Module 1! You’ve taken a huge step in your journey to become digitally smarter.</p>
<p>Over the last lessons, you learned that social engineering is “human hacking” that exploits Authority, Urgency, Trust, and other psychological triggers to bypass even strong technical defenses.</p>
<p>This knowledge is your most powerful tool. By understanding these tricks, you can pause, think, and protect yourself from potential attacks.</p>
<hr/>
<h4>Your Next Steps</h4>
<ol>
  <li>Take the Module 1 Quiz to check your understanding.</li>
  <li>Complete the Reflection Activity to connect learning with your experiences.</li>
  <li>Proceed to the next module for real-world attack vectors.</li>
  <li><em>Next lesson:</em> Psychology Behind the Deception (1.2).</li>
  
</ol>
'''


def upsert_conclusion_and_refs():
    with app.app_context():
        db.create_all()

        # Add a concluding lesson as order 14 for Module 1
        lesson = Lesson.query.filter_by(module_id=1, order=14).first()
        if not lesson:
            lesson = Lesson(
                module_id=1,
                order=14,
                title='Module 1 Conclusion: The Power of an Informed Mindset',
                summary='Wrap-up and next steps for Module 1.',
                content_rich=LESSON_HTML,
                video_url=None,
                video_type=None,
                attachment_urls=json.dumps([]),
                est_time_min=2,
            )
            db.session.add(lesson)
        else:
            lesson.title = 'Module 1 Conclusion: The Power of an Informed Mindset'
            lesson.summary = 'Wrap-up and next steps for Module 1.'
            lesson.content_rich = LESSON_HTML
            lesson.video_url = None
            lesson.video_type = None
            lesson.attachment_urls = json.dumps([])
            lesson.est_time_min = 2

        # Add external references (BBC, IBM, Cialdini article, YouTube refresher)
        refs = [
            (1, 'BBC: Major US Twitter accounts hacked in Bitcoin scam', 'https://www.bbc.com/news/technology-53425822'),
            (2, 'IBM: What is Social Engineering?', 'https://www.ibm.com/topics/social-engineering'),
            (3, 'Cialdini’s 6 Principles of Persuasion (overview)', 'https://people-shift.com/articles/cialdinis-6-principles-of-persuasion/'),
            (4, 'Psychology of Social Engineering (video refresher)', 'https://www.youtube.com/watch?v=P3rbadeF9AI'),
        ]
        for order, label, url in refs:
            ref = Reference.query.filter_by(module_id=1, order=order, label=label).first()
            if not ref:
                db.session.add(Reference(module_id=1, order=order, label=label, url=url))

        # Ensure Reflection placeholder exists for Module 1
        refl = Reflection.query.filter_by(module_id=1).first()
        if not refl:
            refl = Reflection(
                module_id=1,
                prompt='<p>Think of a time you felt pressured online (e.g., urgent email, payment request, giveaway). Which principles were used? How would you respond differently now?</p>',
                rubric='<ul><li>Identify at least one principle (Authority, Urgency, Scarcity, Liking, Social Proof)</li><li>Explain how it influenced your reaction</li><li>Describe a safer alternative response</li></ul>',
                is_required=True,
            )
            db.session.add(refl)

        db.session.commit()
        print('OK: Module 1 conclusion, references, and reflection are set')


if __name__ == '__main__':
    upsert_conclusion_and_refs()




