import os
import sys
import json

# Ensure project root is on path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Stable config
os.environ['FLASK_ENV'] = 'production'

from app import app, db
from data_models.content_models import Lesson
from data_models.progress_models import Quiz, QuizQuestion


LESSON_HTML = '''<h3>Lesson 1.2: The Manipulator's Toolkit</h3>
<p>We\'re diving deeper into the mind of a social engineer and the psychological principles used to manipulate us. Understanding these tricks is your best defense.</p>

<h4>Part 1: Introduction to Psychological Triggers (0:00 - 0:45)</h4>
<p><em>Visuals:</em> Title card \"The Manipulator\'s Toolkit\"; student on phone; icons for Authority, Urgency, Liking, Scarcity around a brain.</p>
<p><em>Narration:</em> Sometimes you feel pressured to act online—that\'s no accident. Social engineers use specific psychological triggers to make us act without thinking.</p>

<h4>Part 2: Authority – The 'Boss' Effect (0:45 - 1:45)</h4>
<p><em>Visuals:</em> Official-looking sender (Registrar/PNP). Fake email with password reset link; suspicious URL highlighted.</p>
<p><em>Narration:</em> We\'re wired to obey authority. Impersonated \"Dean/IT Support\" messages use tone and logos so you click or share info without verifying.</p>

<h4>Part 3: Urgency & Scarcity – The 'Act Fast!' Trap (1:45 - 3:00)</h4>
<p><em>Visuals:</em> Ticking clock; depleting counter. Fake GCash suspension SMS; \"FREE 1000 credits\" with rapidly dropping stock.</p>
<p><em>Narration:</em> Pressure and FOMO rush you so you skip critical thinking. Legit orgs rarely demand immediate action without verification.</p>

<h4>Part 4: Liking & Social Proof – The 'Friendly Face' & 'Everyone's Doing It' (3:00 - 4:15)</h4>
<p><em>Visuals:</em> Message from a \"friend\" asking for urgent GCash; viral giveaway post with many likes.</p>
<p><em>Narration:</em> If it seems to come from someone you like, you drop your guard. Social proof adds \"everyone is doing it\" pressure. Friends\' accounts can be hacked—verify!</p>

<h4>Part 5: Recap and Cialdini\'s Principles (4:15 - 5:30)</h4>
<p>Authority, Urgency, Scarcity, Liking, Social Proof are core influence levers (Cialdini, \"Influence\"). Knowing them builds your mental firewall.</p>
'''


QUIZ_QUESTIONS = [
    {
        'order': 1,
        'question': "Which principle(s) are used in an email from 'Prof. Reyes' saying your portal password expires in 24 hours?",
        'option_a': 'Authority only',
        'option_b': 'Urgency only',
        'option_c': 'Authority and Urgency',
        'option_d': 'Liking and Scarcity',
        'correct_option': 'c',
        'explanation': 'Impersonated authority + time pressure to rush you into clicking.',
    },
    {
        'order': 2,
        'question': 'A post promises FREE 1000 game credits, limited to the first 500 users. What\'s at play?',
        'option_a': 'Scarcity and Liking',
        'option_b': 'Authority and Urgency',
        'option_c': 'Reciprocity and Social Proof',
        'option_d': 'Greed and Authority',
        'correct_option': 'a',
        'explanation': 'Scarcity (limited slots) + Liking (appeal to what you enjoy).',
    },
    {
        'order': 3,
        'question': 'A message from a friend says: Emergency! Please send GCash now. Which principle(s)?',
        'option_a': 'Authority and Scarcity',
        'option_b': 'Liking and Urgency',
        'option_c': 'Commitment and Consistency',
        'option_d': 'Social Proof only',
        'correct_option': 'b',
        'explanation': 'Looks like a trusted friend (Liking) + urgent pressure to act now.',
    },
]


def upsert_lesson_and_quiz():
    with app.app_context():
        db.create_all()

        # Upsert Lesson (use order 13 to avoid clashing with existing 1.2 if present)
        lesson = Lesson.query.filter_by(module_id=1, order=13).first()
        if not lesson:
            lesson = Lesson(
                module_id=1,
                order=13,
                title="The Manipulator's Toolkit",
                summary='Deep dive into authority, urgency, scarcity, liking, and social proof.',
                content_rich=LESSON_HTML,
                video_url='',  # set actual video path when available
                video_type='animated',
                attachment_urls=json.dumps([]),
                est_time_min=6,
            )
            db.session.add(lesson)
        else:
            lesson.title = "The Manipulator's Toolkit"
            lesson.summary = 'Deep dive into authority, urgency, scarcity, liking, and social proof.'
            lesson.content_rich = LESSON_HTML
            lesson.video_url = lesson.video_url or ''
            lesson.video_type = 'animated'
            lesson.attachment_urls = json.dumps([])
            lesson.est_time_min = 6

        # Upsert Quiz for Module 1
        quiz = Quiz.query.filter_by(module_id=1).first()
        if not quiz:
            quiz = Quiz(module_id=1, title='Module 1 Knowledge Check', passing_score=80, shuffle=True)
            db.session.add(quiz)
            db.session.flush()

        # Replace or ensure questions
        existing = {q.order: q for q in QuizQuestion.query.filter_by(quiz_id=quiz.id).all()} if quiz.id else {}
        for qd in QUIZ_QUESTIONS:
            q = existing.get(qd['order'])
            if not q:
                q = QuizQuestion(
                    quiz_id=quiz.id,
                    order=qd['order'],
                    question=qd['question'],
                    option_a=qd['option_a'],
                    option_b=qd['option_b'],
                    option_c=qd['option_c'],
                    option_d=qd['option_d'],
                    correct_option=qd['correct_option'],
                    explanation=qd['explanation'],
                )
                db.session.add(q)
            else:
                q.question = qd['question']
                q.option_a = qd['option_a']
                q.option_b = qd['option_b']
                q.option_c = qd['option_c']
                q.option_d = qd['option_d']
                q.correct_option = qd['correct_option']
                q.explanation = qd['explanation']

        db.session.commit()
        print('OK: Lesson 1.3 and Module 1 quiz seeded')


if __name__ == '__main__':
    upsert_lesson_and_quiz()


