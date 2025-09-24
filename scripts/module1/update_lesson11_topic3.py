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
<h4>Conclusion & Resources</h4>
<p>Great job! You’ve just learned that social engineering isn’t about hacking computers—it’s about human hacking. The best security in the world can’t stop a scammer if they can just trick you into giving them access. That’s why your mindset is your strongest defense.</p>
<p>Now that you know what social engineering is, let's explore why it works so well.</p>
<h5>Resources & For More Info</h5>
<ul>
  <li><strong>Read More:</strong> For a real-world example of a social engineering attack on a large scale, read the BBC article on the “Major US Twitter accounts hacked in Bitcoin scam.” This shows how hackers tricked employees to gain access. <a href="https://www.bbc.com/news/technology-53425822" target="_blank" rel="noopener noreferrer">BBC Article</a></li>
  <li><strong>Learn More:</strong> For a comprehensive guide on the definition of social engineering and why it bypasses technical defenses, check out the article “What is Social Engineering?” from IBM. <a href="https://www.ibm.com/topics/social-engineering" target="_blank" rel="noopener noreferrer">IBM Topic Page</a></li>
  <li><strong>Next Lesson:</strong> You will now move on to Lesson 1.2: The Psychology Behind the Deception.</li>
 </ul>
"""
).strip()


def main():
    with app.app_context():
        db.create_all()
        lesson = Lesson.query.filter_by(module_id=1, order=11).first()
        if not lesson:
            print('Lesson 1.1 not found')
            return

        topic = LessonTopic.query.filter_by(lesson_id=lesson.id, order=3).first()
        if not topic:
            topic = LessonTopic(lesson_id=lesson.id, order=3, title='Lesson Conclusion: What is Social Engineering?')
            db.session.add(topic)
        topic.title = 'Lesson Conclusion: What is Social Engineering?'
        topic.content_rich = CONTENT_HTML
        topic.video_url = None

        db.session.commit()
        print('OK: Lesson 1.1 topic 3 (Conclusion & Resources) updated')


if __name__ == '__main__':
    main()




