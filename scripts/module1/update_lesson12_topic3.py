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
<h4>Module 1 Conclusion: The Power of an Informed Mindset</h4>
<p>Congratulations on completing Module 1! You’ve taken a huge step in your journey to become digitally smarter.</p>
<p>Over the last two lessons, you’ve discovered that social engineering isn’t about hacking computers; it’s about <em>human hacking</em>. You learned how attackers use psychological tactics like <strong>Authority</strong>, <strong>Urgency</strong>, and <strong>Trust</strong> to bypass even the strongest technical defenses.</p>
<p>This knowledge is your most powerful tool. By understanding how these tricks work, you're now better equipped to pause, think, and protect yourself from potential attacks.</p>

<div class="definition-card">
  <div class="card-header">Your Next Steps</div>
  <div class="card-body">
    <ul>
      <li><strong>Take the Module 1 Quiz</strong>: A short check of the key concepts from Lessons 1.1 and 1.2.</li>
      <li><strong>Complete the Reflection Activity</strong>: Connect what you’ve learned to your personal experiences and mindset.</li>
    </ul>
    <p>Your awareness journey has just begun—up next, we’ll go deeper into recognizing real-world attack vectors used by social engineers.</p>
  </div>
  </div>

<h5>Resources & For More Info</h5>
<ul>
  <li><strong>Read More:</strong> A deeper dive into the science behind the tricks: <a href="https://people-shift.com/articles/cialdinis-6-principles-of-persuasion/" target="_blank" rel="noopener noreferrer">Cialdini’s 6 Principles of Persuasion</a>.</li>
  <li><strong>Watch Again:</strong> Quick refresher video explaining mental shortcuts scammers exploit: <a href="https://www.youtube.com/watch?v=P3rbadeF9AI" target="_blank" rel="noopener noreferrer">Psychology of social engineering</a>.</li>
 </ul>
"""
).strip()


def main():
    with app.app_context():
        db.create_all()
        # Lesson 1.2 (order=12)
        lesson = Lesson.query.filter_by(module_id=1, order=12).first()
        if not lesson:
            print('Lesson 1.2 not found')
            return

        # Topic 3: Module 1 Conclusion
        topic = LessonTopic.query.filter_by(lesson_id=lesson.id, order=3).first()
        if not topic:
            topic = LessonTopic(lesson_id=lesson.id, order=3, title='Module 1 Conclusion: The Power of an Informed Mindset')
            db.session.add(topic)
        topic.title = 'Module 1 Conclusion: The Power of an Informed Mindset'
        topic.content_rich = CONTENT_HTML
        topic.video_url = None

        db.session.commit()
        print('OK: Lesson 1.2 topic 3 (Module 1 Conclusion) updated')


if __name__ == '__main__':
    main()




