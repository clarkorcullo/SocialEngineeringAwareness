import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.dirname(CURRENT_DIR)
PROJECT_ROOT = os.path.dirname(SCRIPTS_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ['FLASK_ENV'] = 'production'

from app import app, db
from data_models.content_models import KnowledgeCheckQuestion


QUESTIONS = [
    # 1 (SE Definition)
    {
        'question_text': "(SE Definition) According to Lesson 1.1, which of the following is the most accurate definition of social engineering?",
        'option_a': 'The use of complex code to bypass a digital firewall.',
        'option_b': 'The practice of analyzing social media to improve network security.',
        'option_c': 'The art of manipulating people into giving up confidential information by exploiting psychological tricks.',
        'option_d': 'The process of building better, more secure computer hardware.',
        'correct_answer': 'c',
        'explanation': "Correct! Lesson 1.1 defines social engineering as 'human hacking' that uses psychological tricks to manipulate people.",
    },
    # 2 (Key Distinction)
    {
        'question_text': '(Key Distinction) What is the primary way social engineering differs from a traditional technical hack?',
        'option_a': 'Social engineering is only used for pranks, while technical hacking is for serious crimes.',
        'option_b': 'Social engineering targets the human user to bypass security, while technical hacking targets vulnerabilities in software or systems.',
        'option_c': 'Social engineering requires advanced programming skills, while technical hacking does not.',
        'option_d': 'Social engineering can only be done over the phone, not through email.',
        'correct_answer': 'b',
        'explanation': 'Exactly! The core idea is that social engineers bypass technology by targeting the person. It\'s like being convinced to hand over the key to your own house.',
    },
    # 3 (Psychological Bias)
    {
        'question_text': '(Psychological Bias) You receive an email with the subject line "URGENT: Your Student Portal Password Will Expire in 24 Hours!" The email appears to be from the "Registrar\'s Office" and demands you click a link immediately. This attack primarily uses which two principles?',
        'option_a': 'Liking and Social Proof',
        'option_b': 'Scarcity and Liking',
        'option_c': 'Authority and Urgency',
        'option_d': 'Scarcity and Authority',
        'correct_answer': 'c',
        'explanation': "That's right! This attack uses Authority (pretending to be the Registrar) and Urgency (the 24-hour deadline) to make you act without thinking, just like the example in Lesson 1.2.",
    },
    # 4 (Common Motivation)
    {
        'question_text': '(Common Motivation) Based on the examples in the lessons (Bitcoin scam, GCash requests), what is a common motivation for social engineers?',
        'option_a': "To test a company's firewall for weaknesses.",
        'option_b': 'To make new friends and connections online.',
        'option_c': 'To gain access to information or resources for personal or financial benefit.',
        'option_d': 'To help users become more skeptical and informed.',
        'correct_answer': 'c',
        'explanation': 'Correct. The examples consistently show that attackers are trying to get something valuable, whether it\'s money, account access, or personal information.',
    },
    # 5 (Concept Identification) True/False
    {
        'question_text': '(Concept Identification) True or False: The lessons state that a strong firewall and antivirus software are enough to stop all social engineering attacks.',
        'option_a': 'True',
        'option_b': 'False',
        'option_c': '—',
        'option_d': '—',
        'correct_answer': 'b',
        'explanation': "Correct, this is false. Lesson 1.1 emphasizes that social engineering's main strength is its ability to bypass technical defenses by targeting the user directly.",
    },
    # 6 (Psychological Bias)
    {
        'question_text': '(Psychological Bias) A pop-up ad for a mobile game says: "🔥 FREE 1000 GEMS! 🔥 Limited to the first 500 players! Claim yours before they\'re gone!" This tactic relies on the principle of:',
        'option_a': 'Authority',
        'option_b': 'Liking',
        'option_c': 'Scarcity',
        'option_d': 'Social Proof',
        'correct_answer': 'c',
        'explanation': "Perfect! By claiming the offer is 'limited to the first 500 players,' the scam creates a sense of Scarcity to pressure you into acting quickly.",
    },
    # 7 (Psychological Bias)
    {
        'question_text': '(Psychological Bias) You get a message on Messenger from a classmate that says, "Hey, urgent! My GCash is down, please send ₱500 to this number. I\'ll pay you back tomorrow!" This scam primarily exploits which psychological principle?',
        'option_a': 'Authority',
        'option_b': 'Scarcity',
        'option_c': 'Liking',
        'option_d': 'Social Proof',
        'correct_answer': 'c',
        'explanation': 'That\'s it! Because the message appears to be from someone you know and trust (a classmate), it is exploiting the principle of Liking to lower your guard.',
    },
    # 8 (Concept Identification)
    {
        'question_text': '(Concept Identification) The lessons refer to social engineering as "human hacking" because it:',
        'option_a': 'Requires the hacker to be physically present.',
        'option_b': 'Can only be done by very friendly and popular people.',
        'option_c': 'Targets people\'s natural tendencies and psychology instead of computer code.',
        'option_d': 'Is a legal method for testing security.',
        'correct_answer': 'c',
        'explanation': "Yes! This is the central concept from Lesson 1.1. It's called 'human hacking' because it exploits our brains 'shortcuts' and natural tendencies.",
    },
    # 9 (Key Distinction)
    {
        'question_text': '(Key Distinction) Which of these scenarios describes a social engineering attack, as explained in the module?',
        'option_a': 'A hacker discovers a flaw in a website\'s code that allows them to access a database.',
        'option_b': 'A scammer calls an employee, pretends to be from the IT department, and convinces them to reveal their password.',
        'option_c': 'A programmer writes a script that automatically tries thousands of different passwords on a login page.',
        'option_d': 'A network administrator installs a new firewall to block malicious traffic.',
        'correct_answer': 'b',
        'explanation': 'Correct! This is a classic example of social engineering where the attacker uses deception and impersonation to manipulate a person into compromising security.',
    },
    # 10 (Psychological Bias)
    {
        'question_text': '(Psychological Bias) A scammer creates a fake social media post for a giveaway, using bots to add thousands of likes and comments that say "It works! I got my prize!" to convince real users to participate. This is a clear example of an attacker using:',
        'option_a': 'Authority',
        'option_b': 'Social Proof',
        'option_c': 'Urgency',
        'option_d': 'Liking',
        'correct_answer': 'b',
        'explanation': "Exactly! This tactic uses Social Proof to make the scam seem legitimate because 'everyone else is doing it' and appears to be winning.",
    },
]


def upsert_questions():
    with app.app_context():
        db.create_all()
        module_id = 1

        # Delete existing Module 1 knowledge check questions to avoid conflicts
        try:
            KnowledgeCheckQuestion.query.filter_by(module_id=module_id).delete()
            db.session.commit()
        except Exception:
            db.session.rollback()

        # Insert fresh questions
        for qd in QUESTIONS:
            payload = dict(qd)
            payload['module_id'] = module_id
            payload['question_set'] = 1
            db.session.add(KnowledgeCheckQuestion(**payload))
        db.session.commit()
        print('OK: Module 1 knowledge check (10 items) seeded (replaced old set)')


if __name__ == '__main__':
    upsert_questions()




