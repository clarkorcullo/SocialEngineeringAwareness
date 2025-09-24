import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ['FLASK_ENV'] = 'production'

from app import app, db
from data_models.content_models import Reflection


PROMPT_HTML = '''<h3>Module 1 Reflection: "Could This Happen to Me?"</h3>
<p>Now that you’ve completed Module 1, take a few minutes to reflect on how social engineering shows up in your own life. This isn’t just theory—it's about preparing yourself to respond wisely.</p>
<ol>
  <li>Think about a time when someone tried to get you to act quickly, trust them blindly, or give out personal information—online or offline. What happened?</li>
  <li>Now that you’ve completed this module, do you think it might have been a social engineering attempt?</li>
  <li>How did you respond then, and how would you act differently now?</li>
  <li><strong>BONUS:</strong> Share one “aha moment” from this module. What surprised you the most about social engineering, and what habit or mindset will you change starting today?</li>
  
</ol>
'''

RUBRIC_HTML = '''<h4>Reflection Rubric (what we’re looking for)</h4>
<ul>
  <li><strong>Clear scenario:</strong> Describe a real or likely situation where pressure, trust, or data sharing was involved.</li>
  <li><strong>Correct mapping:</strong> Identify the psychological principle(s) involved (e.g., Authority, Urgency, Scarcity, Liking, Social Proof).</li>
  <li><strong>Self-awareness:</strong> Compare your past reaction with how you would respond now.</li>
  <li><strong>Actionable change:</strong> State one mindset or habit you’ll adopt going forward.</li>
</ul>
'''


def upsert_reflection():
    with app.app_context():
        db.create_all()
        refl = Reflection.query.filter_by(module_id=1).first()
        if not refl:
            refl = Reflection(module_id=1, prompt=PROMPT_HTML, rubric=RUBRIC_HTML, is_required=True)
            db.session.add(refl)
        else:
            refl.prompt = PROMPT_HTML
            refl.rubric = RUBRIC_HTML
            refl.is_required = True
        db.session.commit()
        print('OK: Module 1 reflection updated')


if __name__ == '__main__':
    upsert_reflection()




