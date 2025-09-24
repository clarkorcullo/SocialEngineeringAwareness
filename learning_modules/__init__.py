"""
Modules package for Social Engineering Awareness Program
Contains individual module content and knowledge check questions
"""

# Module 1 legacy imports removed (now DB-backed). Keep None placeholders for compatibility.
Module1Content = None
Module1Questions = None

from .module2 import Module2Content, Module2Questions
from .module3 import Module3Content, Module3Questions
from .module4 import Module4Content, Module4Questions
from .module5 import Module5Content, Module5Questions
from .final_assessment import FinalAssessmentContent, FinalAssessmentQuestions

__all__ = [
    'Module1Content', 'Module1Questions',
    'Module2Content', 'Module2Questions',
    'Module3Content', 'Module3Questions',
    'Module4Content', 'Module4Questions',
    'Module5Content', 'Module5Questions',
    'FinalAssessmentContent', 'FinalAssessmentQuestions'
]

