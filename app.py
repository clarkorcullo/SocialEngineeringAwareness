"""
🛡️ SOCIAL ENGINEERING AWARENESS PROGRAM
========================================

Main Flask application for the Social Engineering Awareness Program.
This file contains all routes, middleware, and application configuration.

ARCHITECTURE:
- Clean Architecture with Service Layer Pattern
- Object-Oriented Programming principles
- Separation of concerns between routes and business logic
- Comprehensive error handling and logging

ORGANIZATION:
1. IMPORTS AND SETUP
2. CONFIGURATION AND INITIALIZATION
3. DATABASE INITIALIZATION
4. AUTHENTICATION ROUTES
5. LEARNING ROUTES
6. ASSESSMENT ROUTES
7. SIMULATION ROUTES
8. PROGRESS AND ANALYTICS ROUTES
9. SYSTEM ROUTES
10. ERROR HANDLERS
11. APPLICATION ENTRY POINT

Author: Capstone Project Team
Version: 1.0.0
License: MIT
"""

# =============================================================================
# 1. IMPORTS AND SETUP
# =============================================================================

# Standard library imports
import os
import sys
import logging
from datetime import datetime, timedelta
import random
import json
import secrets

# Third-party imports
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.middleware.proxy_fix import ProxyFix
from sqlalchemy import text

# Local application imports
from data_models.base_models import db
from data_models import (
    User, PasswordResetToken, Module, KnowledgeCheckQuestion, 
    FinalAssessmentQuestion, UserProgress, AssessmentResult, 
    SimulationResult, FeedbackSurvey
)
from business_services import (
    UserService, AssessmentService, SimulationService
)
from config import config

# =============================================================================
# 2. LOGGING CONFIGURATION
# =============================================================================

def setup_logging():
    """
    Configure comprehensive logging for the application.
    
    Features:
    - Console and file output
    - UTF-8 encoding support
    - Configurable log levels
    - Structured formatting
    
    Returns:
        logging.Logger: Configured logger instance
    """
    log_level = os.environ.get('LOG_LEVEL', 'INFO')
    log_file = os.environ.get('LOG_FILE', 'app.log')
    
    # Create formatter that handles Unicode properly
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Console handler with UTF-8 encoding
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # File handler with UTF-8 encoding
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    return logging.getLogger(__name__)

# Initialize logging
logger = setup_logging()

# =============================================================================
# 3. FLASK APPLICATION SETUP
# =============================================================================

# Create Flask application instance
app = Flask(__name__)

# Load environment-based configuration
config_name = os.environ.get('FLASK_ENV', 'production')
app.config.from_object(config[config_name])

# Configure reverse proxy for production deployment (Render/Heroku)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# =============================================================================
# 4. EXTENSIONS AND SERVICES INITIALIZATION
# =============================================================================

# Initialize database
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize business services
user_service = UserService()
assessment_service = AssessmentService()
simulation_service = SimulationService()

# =============================================================================
# 5. DATABASE INITIALIZATION FUNCTIONS
# =============================================================================

def init_database():
    """
    Initialize database with all models and create default data.
    
    This function:
    - Creates all database tables
    - Populates default educational content
    - Creates admin user if not exists
    - Sets up initial modules and questions
    
    Raises:
        Exception: If database initialization fails
    """
    try:
        db.create_all()
        create_default_data()
        logger.info("[SUCCESS] Database initialized successfully")
    except Exception as e:
        logger.error(f"[ERROR] Database initialization error: {e}")
        raise

def create_default_data():
    """
    Create default application data including admin user, modules, and questions.
    
    This function ensures the application has:
    - Default administrator account
    - All educational modules
    - Assessment questions
    - Initial configuration
    
    The function is idempotent - it won't create duplicates if data already exists.
    """
    try:
        # =====================================================================
        # ADMIN USER CREATION
        # =====================================================================
        admin_user = User.get_by_username('administrator')
        if not admin_user:
            try:
                admin_data = {
                    'username': app.config.get('DEFAULT_ADMIN_USERNAME', 'administrator'),
                    'email': app.config.get('DEFAULT_ADMIN_EMAIL', 'admin@mmdc.edu.ph'),
                    'password': app.config.get('DEFAULT_ADMIN_PASSWORD', 'Admin123!@#2025'),
                    'full_name': 'System Administrator',
                    'specialization': 'Information Technology',
                    'year_level': '4th Year'
                }
                user_service.create_user(admin_data)
                logger.info("[SUCCESS] Admin user created (administrator)")
            except ValueError as ve:
                if "already exists" in str(ve):
                    logger.info("[SUCCESS] Admin user already exists (administrator)")
                else:
                    logger.warning(f"[WARNING] Admin user creation issue: {ve}")
        else:
            logger.info("[SUCCESS] Admin user already exists (administrator)")

        # Update admin password if environment variable is set
        desired_pw = os.environ.get('ADMIN_PASSWORD')
        if desired_pw and admin_user:
            try:
                if admin_user.set_password(desired_pw):
                    admin_user.save()
                    logger.info("[SUCCESS] Admin password refreshed from ADMIN_PASSWORD env")
            except Exception as pw_e:
                logger.warning(f"[WARNING] Could not refresh admin password: {pw_e}")
        
        # =====================================================================
        # EDUCATIONAL MODULES CREATION
        # =====================================================================
        if Module.count() == 0:
            create_default_modules()
            logger.info("[SUCCESS] Default modules created")
        else:
            logger.info("[SUCCESS] Modules already exist")
        
        # =====================================================================
        # ASSESSMENT QUESTIONS CREATION
        # =====================================================================
        if KnowledgeCheckQuestion.count() == 0:
            create_default_questions()
            logger.info("[SUCCESS] Default questions created")
        else:
            logger.info("[SUCCESS] Questions already exist")
            
    except Exception as e:
        logger.error(f"[ERROR] Error creating default data: {e}")
        raise

# =============================================================================
# 6. FLASK-LOGIN USER LOADER
# =============================================================================

@login_manager.user_loader
def load_user(user_id):
    """
    Load user for Flask-Login authentication.
    
    Args:
        user_id (str): User ID from session
        
    Returns:
        User: User object if found, None otherwise
    """
    try:
        return User.get_by_id(int(user_id))
    except Exception as e:
        logger.error(f"Error loading user {user_id}: {e}")
        return None

# =============================================================================
# 7. DATABASE INITIALIZATION ON STARTUP
# =============================================================================

# Ensure database is initialized when running under WSGI servers (e.g., Render)
try:
    with app.app_context():
        init_database()
except Exception as e:
    logger.error(f"[ERROR] Database init on import failed: {e}")

# =============================================================================
# 8. APPLICATION FACTORY PATTERN
# =============================================================================

# Initialize database and create default data
with app.app_context():
    try:
        init_database()
        logger.info("[SUCCESS] Application initialized successfully")
    except Exception as e:
        logger.error(f"[ERROR] Application initialization failed: {e}")
        # Continue anyway - the app might still work

# =============================================================================
# 9. EDUCATIONAL CONTENT CREATION FUNCTIONS
# =============================================================================

def create_default_modules():
    """
    Create default learning modules with content from modules folder.
    
    This function:
    - Imports content from learning_modules/
    - Creates Module objects in database
    - Sets up simulation types for applicable modules
    - Handles fallback content if imports fail
    """
    try:
        # Import module content classes
        from learning_modules import (
            Module1Content, Module2Content, Module3Content, Module4Content,
            Module5Content, Module6Content, Module7Content, FinalAssessmentContent
        )
        
        # Module content classes
        module_classes = [
            Module1Content, Module2Content, Module3Content, Module4Content,
            Module5Content, Module6Content, Module7Content, FinalAssessmentContent
        ]
        
        for i, module_class in enumerate(module_classes, 1):
            # Get content from module class
            content_data = module_class.get_content()
            
            # Create module data
            module_data = {
                'name': content_data['title'],
                'description': content_data['description'],
                'content': content_data['content'],
                'order': i,
                'has_simulation': i in [2, 3, 4, 5],  # Modules 2-5 have simulations
                'simulation_type': 'quid_pro_quo' if i == 2 else 'phishing' if i == 3 else 'pretexting' if i == 4 else 'baiting' if i == 5 else None
            }
            
            # Create and save module
            module = Module(**module_data)
            if module.save():
                logger.info(f"[SUCCESS] Created module {i}: {content_data['title']}")
            else:
                logger.warning(f"[ERROR] Failed to create module {i}")
                
    except Exception as e:
        logger.error(f"[ERROR] Error creating modules: {e}")
        # Fallback to basic modules if import fails
        create_fallback_modules()

def create_fallback_modules():
    """
    Create basic modules as fallback if content imports fail.
    
    This ensures the application always has some content available,
    even if the learning_modules package has issues.
    """
    modules_data = [
        {
            'name': 'Introduction to Social Engineering',
            'description': 'Understanding the basics of social engineering attacks',
            'content': 'Social engineering is a manipulation technique that exploits human error to gain private information...',
            'order': 1,
            'has_simulation': False
        },
        {
            'name': 'Types of Social Engineering Attacks',
            'description': 'Learn about different types of social engineering attacks',
            'content': 'There are several types of social engineering attacks...',
            'order': 2,
            'has_simulation': True,
            'simulation_type': 'phishing'
        },
        {
            'name': 'Phishing Attacks',
            'description': 'Learn about phishing techniques and prevention',
            'content': 'Phishing is a type of social engineering attack where attackers impersonate legitimate entities...',
            'order': 3,
            'has_simulation': True,
            'simulation_type': 'phishing'
        },
        {
            'name': 'Pretexting and Impersonation',
            'description': 'Understanding pretexting and impersonation techniques',
            'content': 'Pretexting involves creating a fabricated scenario...',
            'order': 4,
            'has_simulation': True,
            'simulation_type': 'pretexting'
        },
        {
            'name': 'Baiting and Quid Pro Quo',
            'description': 'Learn about baiting and quid pro quo attacks',
            'content': 'Baiting involves leaving a physical device...',
            'order': 5,
            'has_simulation': True,
            'simulation_type': 'baiting'
        },
        {
            'name': 'Advanced Techniques',
            'description': 'Advanced social engineering techniques and countermeasures',
            'content': 'Advanced social engineering techniques include...',
            'order': 6,
            'has_simulation': False
        },
        {
            'name': 'Incident Response',
            'description': 'How to respond to social engineering incidents',
            'content': 'When a social engineering incident occurs...',
            'order': 7,
            'has_simulation': False
        }
    ]
    
    for module_data in modules_data:
        module = Module(**module_data)
        if module.save():
            logger.info(f"[SUCCESS] Created fallback module: {module_data['name']}")
        else:
            logger.warning(f"[ERROR] Failed to create fallback module: {module_data['name']}")

def create_default_questions():
    """
    Create default assessment questions for all modules.
    
    This function:
    - Imports question sets from learning_modules/
    - Creates KnowledgeCheckQuestion objects
    - Links questions to appropriate modules
    - Handles fallback questions if imports fail
    """
    try:
        # Import question classes
        from learning_modules import (
            Module1Questions, Module2Questions, Module3Questions, Module4Questions,
            Module5Questions, Module6Questions, Module7Questions, FinalAssessmentQuestions
        )
        
        # Question classes mapping
        question_classes = [
            Module1Questions, Module2Questions, Module3Questions, Module4Questions,
            Module5Questions, Module6Questions, Module7Questions, FinalAssessmentQuestions
        ]
        
        for module_id, question_class in enumerate(question_classes, 1):
            # Get questions from module class
            questions_data = question_class.get_question_set_1()
            
            for question_data in questions_data:
                # Add module_id to question data
                question_data['module_id'] = module_id
                
                # Remove any fields that are not in the KnowledgeCheckQuestion model
                if 'module_source' in question_data:
                    del question_data['module_source']
                
                # Create and save question
                question = KnowledgeCheckQuestion(**question_data)
                if question.save():
                    logger.info(f"[SUCCESS] Created question for module {module_id}")
                else:
                    logger.warning(f"[ERROR] Failed to create question for module {module_id}")
                    
    except Exception as e:
        logger.error(f"[ERROR] Error creating questions: {e}")
        create_fallback_questions()

def create_fallback_questions():
    """
    Create basic questions as fallback if content imports fail.
    
    Ensures the application always has assessment questions available.
    """
    fallback_questions = [
        {
            'question': 'What is social engineering?',
            'option_a': 'A type of software',
            'option_b': 'A manipulation technique that exploits human error',
            'option_c': 'A hardware component',
            'option_d': 'A programming language',
            'correct_answer': 'b',
            'explanation': 'Social engineering is a manipulation technique that exploits human error to gain private information.',
            'module_id': 1
        },
        {
            'question': 'Which of the following is a common social engineering attack?',
            'option_a': 'Phishing',
            'option_b': 'Firewall',
            'option_c': 'Antivirus',
            'option_d': 'Encryption',
            'correct_answer': 'a',
            'explanation': 'Phishing is one of the most common social engineering attacks.',
            'module_id': 2
        }
    ]
    
    for question_data in fallback_questions:
        question = KnowledgeCheckQuestion(**question_data)
        if question.save():
            logger.info(f"[SUCCESS] Created fallback question: {question_data['question'][:50]}...")
        else:
            logger.warning(f"[ERROR] Failed to create fallback question")

# =============================================================================
# 10. ROUTE DEFINITIONS
# =============================================================================

# =============================================================================
# 10.1 AUTHENTICATION ROUTES
# =============================================================================

@app.route('/')
def index():
    """
    Home page route - displays the main landing page.
    
    Features:
    - Public access (no login required)
    - Responsive design with cybersecurity theme
    - Call-to-action buttons for registration/login
    - Program overview and features
    
    Returns:
        str: Rendered index.html template
    """
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error loading index page: {e}")
        # Don't redirect to login on error, just show the page
        return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    User registration route - handles new user account creation.
    
    Features:
    - Comprehensive form validation
    - Password strength requirements
    - Email format validation
    - Duplicate username/email checking
    - Secure password hashing
    
    Methods:
        GET: Display registration form
        POST: Process registration data
        
    Returns:
        str: Rendered template or redirect
    """
    if request.method == 'POST':
        try:
            # Get and validate form data
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            full_name = request.form.get('full_name', '').strip()
            specialization = request.form.get('specialization', '')
            year_level = request.form.get('year_level', '')
            
            # Validate required fields
            if not all([username, email, password, confirm_password, full_name, specialization, year_level]):
                flash('All fields are required.', 'error')
                logger.warning(f"Registration failed: Missing required fields for user {username}")
                return render_template('register.html', form_data=request.form)
            
            # Validate password confirmation
            if password != confirm_password:
                flash('Passwords do not match.', 'error')
                logger.warning(f"Registration failed: Password mismatch for user {username}")
                return render_template('register.html', form_data=request.form)
            
            # Create user data
            user_data = {
                'username': username,
                'email': email,
                'password': password,
                'full_name': full_name,
                'specialization': specialization,
                'year_level': year_level
            }
            
            try:
                user = user_service.create_user(user_data)
                if user:
                    flash('Registration successful! Please login.', 'success')
                    logger.info(f"User {username} registered successfully")
                    return redirect(url_for('login'))
            except ValueError as ve:
                flash(str(ve), 'error')
                logger.warning(f"Registration failed for user {username}: {ve}")
                
        except ValueError as e:
            flash(str(e), 'error')
            logger.error(f"Registration failed: {e}")
        except Exception as e:
            flash(f'Registration error: {e}', 'error')
            logger.error(f"Registration failed: {e}")
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    User login route - handles user authentication.
    
    Features:
    - Secure password verification
    - Session management
    - Login attempt logging
    - Redirect to dashboard on success
    
    Methods:
        GET: Display login form
        POST: Process login credentials
        
    Returns:
        str: Rendered template or redirect
    """
    if request.method == 'POST':
        try:
            username = request.form['username']
            password = request.form['password']
            
            user = user_service.authenticate_user(username, password)
            if user:
                login_user(user)
                flash('Login successful!', 'success')
                logger.info(f"User {username} logged in successfully")
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password.', 'error')
                logger.warning(f"Login failed for user {username}: Invalid credentials")
                
        except Exception as e:
            flash(f'Login error: {e}', 'error')
            logger.error(f"Login failed: {e}")
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """
    User logout route - handles user session termination.
    
    Features:
    - Graceful logout for authenticated users
    - Session cleanup
    - Informative messages for different scenarios
    - No authentication required (fixes 500 error issue)
    
    Returns:
        str: Redirect to home page
    """
    try:
        if current_user.is_authenticated:
            username = current_user.username
            logout_user()
            flash('You have been logged out.', 'info')
            logger.info(f"User {username} logged out successfully")
        else:
            flash('You were already logged out.', 'info')
            logger.info("Logout attempted for non-authenticated user")
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        flash('Logout completed.', 'info')
    finally:
        # Clear any session data
        session.clear()
    
    return redirect(url_for('index'))

# =============================================================================
# 10.2 LEARNING ROUTES
# =============================================================================

@app.route('/dashboard')
@login_required
def dashboard():
    """
    User dashboard route - displays user progress and learning overview.
    
    Features:
    - Comprehensive progress tracking
    - Module completion status
    - Recent activity feed
    - Performance analytics
    - Access control for modules
    
    Returns:
        str: Rendered dashboard template
    """
    try:
        # Get user statistics using service
        user_stats = user_service.get_user_statistics(current_user.id)
        
        # Get user progress
        user_progress = UserProgress.get_user_progress(current_user.id)
        
        # Get modules
        modules = Module.get_all_ordered()
        
        # Get total modules count
        total_modules = Module.count()
        
        # Get properly completed modules using validation
        completed_module_ids = user_service.get_user_completed_modules(current_user.id)
        completed_modules = len(completed_module_ids)
        
        # Get final assessment result
        final_result = AssessmentResult.query.filter_by(
            user_id=current_user.id, 
            assessment_type='final_assessment', 
            passed=True
        ).first()
        
        # Get survey completion status
        survey_completed = FeedbackSurvey.query.filter_by(user_id=current_user.id).first()
        
        # Calculate accessible modules (modules 1 to total_modules)
        accessible_modules = []
        for i in range(1, total_modules + 1):  # Modules 1 to total_modules
            if i == 1:
                # First module is always accessible
                accessible_modules.append(True)
            else:
                # Other modules are accessible if previous module is fully completed
                previous_module_completed = user_service.is_module_fully_completed(current_user.id, i-1)
                accessible_modules.append(previous_module_completed)
        
        # Build recent activity feed (simulations, assessments, module completions, surveys)
        recent_activities = []

        # Simulations
        sim_results = SimulationResult.query.filter_by(
            user_id=current_user.id
        ).order_by(SimulationResult.created_at.desc()).limit(10).all()
        for sim in sim_results:
            recent_activities.append({
                'type': 'simulation',
                'title': f"{(sim.simulation_type or '').replace('_', ' ').title()} Simulation",
                'detail': f"Score: {sim.score}%",
                'badge_text': 'Completed' if sim.completed else 'In Progress',
                'badge_class': 'bg-success' if sim.completed else 'bg-warning',
                'timestamp': sim.updated_at or sim.created_at
            })

        # Assessments (knowledge checks, final, baseline)
        assess_results = AssessmentResult.query.filter_by(user_id=current_user.id)\
            .order_by(AssessmentResult.created_at.desc()).limit(10).all()
        for ar in assess_results:
            module_name = None
            if ar.module_id:
                m = Module.get_by_id(ar.module_id)
                module_name = m.name if m else None
            assessment_label = {
                'knowledge_check': 'Knowledge Check',
                'final_assessment': 'Final Assessment',
                'baseline': 'Baseline Assessment',
                'follow_up': 'Follow-up Assessment'
            }.get(ar.assessment_type, 'Assessment')
            title = f"{assessment_label}" + (f" - {module_name}" if module_name else '')
            percent = int((ar.score / ar.total_questions) * 100) if ar.total_questions else ar.score
            recent_activities.append({
                'type': 'assessment',
                'title': title,
                'detail': f"Score: {percent}% ({ar.correct_answers}/{ar.total_questions})",
                'badge_text': 'Passed' if getattr(ar, 'passed', False) else 'Failed',
                'badge_class': 'bg-success' if getattr(ar, 'passed', False) else 'bg-danger',
                'timestamp': ar.created_at
            })

        # Module completions
        completed_progress = UserProgress.query.filter_by(
            user_id=current_user.id,
            status='completed'
        ).order_by(UserProgress.completed_at.desc()).limit(10).all()
        for up in completed_progress:
            m = Module.get_by_id(up.module_id)
            recent_activities.append({
                'type': 'module',
                'title': f"Module Completed - {m.name if m else f'ID {up.module_id}'}",
                'detail': f"Score: {up.score}%",
                'badge_text': 'Completed',
                'badge_class': 'bg-success',
                'timestamp': up.completed_at or up.updated_at or up.created_at
            })

        # Surveys
        surveys = FeedbackSurvey.query.filter_by(user_id=current_user.id)\
            .order_by(FeedbackSurvey.created_at.desc()).limit(10).all()
        for s in surveys:
            m = Module.get_by_id(s.module_id) if s.module_id else None
            recent_activities.append({
                'type': 'survey',
                'title': f"Feedback Submitted" + (f" - {m.name}" if m else ''),
                'detail': f"Rating: {s.rating}/5",
                'badge_text': 'Submitted',
                'badge_class': 'bg-info',
                'timestamp': s.created_at
            })

        # Sort by timestamp and take top 5
        recent_activities = sorted(
            recent_activities,
            key=lambda a: a['timestamp'] or datetime.utcnow(),
            reverse=True
        )[:5]
        
        # Calculate average score from assessment results
        assessment_results = AssessmentResult.query.filter_by(user_id=current_user.id).all()
        if assessment_results:
            total_score = sum(result.score for result in assessment_results)
            total_questions = sum(result.total_questions for result in assessment_results)
            average_score = int((total_score / total_questions) * 100) if total_questions > 0 else 0
        else:
            average_score = 0
        
        # Calculate total time spent (estimate: 30 minutes per completed module)
        total_time_spent = completed_modules * 30
        
        return render_template('dashboard.html', 
                             user_stats=user_stats,
                             user_progress=user_progress,
                             modules=modules,
                             completed_modules=completed_modules,
                             completed_module_ids=completed_module_ids,
                             total_modules=total_modules,
                             final_result=final_result,
                             survey_completed=survey_completed,
                             accessible_modules=accessible_modules,
                             recent_activities=recent_activities,
                             average_score=average_score,
                             total_time_spent=total_time_spent)
    except Exception as e:
        flash(f'Error loading dashboard: {e}', 'error')
        logger.error(f"Error loading dashboard: {e}")
        return redirect(url_for('index'))

@app.route('/module/<int:module_id>')
@login_required
def module(module_id):
    """
    Module view route - displays educational content for a specific module.
    
    Features:
    - Progressive module access control
    - Interactive content display
    - Progress tracking
    - Knowledge check integration
    - Simulation access for applicable modules
    
    Args:
        module_id (int): ID of the module to display
        
    Returns:
        str: Rendered module template or redirect
    """
    try:
        module_obj = Module.get_by_id(module_id)
        if not module_obj:
            flash('Module not found.', 'error')
            logger.warning(f"Module {module_id} not found")
            return redirect(url_for('dashboard'))
            
        # Check if user can access this module
        if module_id == 1:
            # First module is always accessible
            pass
        else:
            # Check if previous module is fully completed
            previous_module_completed = user_service.is_module_fully_completed(current_user.id, module_id - 1)
            if not previous_module_completed:
                flash('You must complete the previous module before accessing this one.', 'warning')
                logger.warning(f"User {current_user.username} attempted to access module {module_id} without completing module {module_id - 1}")
                return redirect(url_for('dashboard'))
        
        # Get user progress for this module
        progress = UserProgress.get_module_progress(current_user.id, module_id)
        if not progress:
            progress = UserProgress(
                user_id=current_user.id,
                module_id=module_id,
                status='not_started'
            )
            progress.save()
        
        # Get knowledge check score for this module
        knowledge_check_result = AssessmentResult.query.filter_by(
            user_id=current_user.id,
            module_id=module_id,
            assessment_type='knowledge_check'
        ).order_by(AssessmentResult.created_at.desc()).first()
        
        # Calculate percentage score
        if knowledge_check_result:
            knowledge_check_score = int((knowledge_check_result.score / knowledge_check_result.total_questions) * 100)
        else:
            knowledge_check_score = 0
        
        return render_template('module.html', 
                             module=module_obj,
                             progress=progress, 
                             knowledge_check_score=knowledge_check_score)
    except Exception as e:
        flash(f'Error loading module: {e}', 'error')
        logger.error(f"Error loading module {module_id}: {e}")
        return redirect(url_for('dashboard'))

# =============================================================================
# 10.3 ASSESSMENT ROUTES
# =============================================================================

@app.route('/assessment/<int:module_id>')
@login_required
def assessment(module_id):
    """
    Module assessment route - displays knowledge check for a specific module.
    
    Features:
    - Dynamic question generation
    - Progress validation
    - Access control
    - Assessment state management
    
    Args:
        module_id (int): ID of the module for assessment
        
    Returns:
        str: Rendered assessment template or redirect
    """
    try:
        # Get module
        module_obj = Module.get_by_id(module_id)
        if not module_obj:
            flash('Module not found.', 'error')
            return redirect(url_for('dashboard'))
        
        # Check if user can access this module
        if module_id > 1:
            previous_module_completed = user_service.is_module_fully_completed(current_user.id, module_id - 1)
            if not previous_module_completed:
                flash('You must complete the previous module first.', 'warning')
                return redirect(url_for('dashboard'))
        
        # Get questions for this module
        questions = KnowledgeCheckQuestion.query.filter_by(module_id=module_id).all()
        if not questions:
            flash('No questions available for this module.', 'error')
            return redirect(url_for('module', module_id=module_id))
        
        # Shuffle questions for variety
        random.shuffle(questions)
        
        return render_template('assessment_simple.html', 
                             module=module_obj,
                             questions=questions,
                             module_id=module_id)
    except Exception as e:
        flash(f'Error loading assessment: {e}', 'error')
        logger.error(f"Error loading assessment for module {module_id}: {e}")
        return redirect(url_for('dashboard'))

@app.route('/submit_assessment/<int:module_id>', methods=['POST'])
@login_required
def submit_assessment(module_id):
    """
    Submit assessment answers and calculate results.
    
    Features:
    - Answer validation and scoring
    - Progress tracking
    - Detailed feedback
    - Result storage
    
    Args:
        module_id (int): ID of the module for assessment
        
    Returns:
        str: Rendered result template or redirect
    """
    try:
        # Get module
        module_obj = Module.get_by_id(module_id)
        if not module_obj:
            flash('Module not found.', 'error')
            return redirect(url_for('dashboard'))
        
        # Get questions for this module
        questions = KnowledgeCheckQuestion.query.filter_by(module_id=module_id).all()
        if not questions:
            flash('No questions available for this module.', 'error')
            return redirect(url_for('module', module_id=module_id))
        
        # Process answers
        answers = {}
        correct_answers = 0
        total_questions = len(questions)
        
        for question in questions:
            answer = request.form.get(f'question_{question.id}')
            answers[question.id] = answer
            
            if answer == question.correct_answer:
                correct_answers += 1
        
        # Calculate score
        score = correct_answers
        percentage = int((correct_answers / total_questions) * 100)
        
        # Determine if passed (80% threshold)
        passed = percentage >= app.config.get('KNOWLEDGE_CHECK_PASSING_SCORE', 80)
        
        # Create assessment result
        result = AssessmentResult(
            user_id=current_user.id,
            module_id=module_id,
            assessment_type='knowledge_check',
            score=score,
            total_questions=total_questions,
            correct_answers=correct_answers,
            passed=passed
        )
        
        if result.save():
            # Update module progress
            progress = UserProgress.get_module_progress(current_user.id, module_id)
            if progress:
                progress.score = percentage
                if passed:
                    progress.status = 'completed'
                    progress.completed_at = datetime.now()
                progress.save()
            
            flash(f'Assessment completed! Score: {percentage}%', 'success' if passed else 'warning')
            logger.info(f"User {current_user.username} completed assessment for module {module_id} with score {percentage}%")
            
            return render_template('assessment_result.html', 
                                 module=module_obj,
                                 score=percentage,
                                 total_questions=total_questions,
                                 correct_answers=correct_answers,
                                 passed=passed,
                                 questions=questions,
                                 answers=answers)
        else:
            flash('Error saving assessment results.', 'error')
            return redirect(url_for('module', module_id=module_id))
            
    except Exception as e:
        flash(f'Error submitting assessment: {e}', 'error')
        logger.error(f"Error submitting assessment for module {module_id}: {e}")
        return redirect(url_for('dashboard'))

# =============================================================================
# 10.4 SIMULATION ROUTES
# =============================================================================

@app.route('/simulation/<simulation_type>')
@login_required
def simulation(simulation_type):
    """
    Simulation route - displays interactive social engineering scenarios.
    
    Features:
    - Dynamic scenario generation
    - Real-time feedback
    - Progress tracking
    - Educational content integration
    
    Args:
        simulation_type (str): Type of simulation (phishing, pretexting, etc.)
        
    Returns:
        str: Rendered simulation template or redirect
    """
    try:
        # Validate simulation type
        valid_types = ['phishing', 'pretexting', 'baiting', 'quid_pro_quo']
        if simulation_type not in valid_types:
            flash('Invalid simulation type.', 'error')
            return redirect(url_for('dashboard'))
        
        # Get simulation data
        simulation_data = simulation_service.get_simulation_data(simulation_type)
        if not simulation_data:
            flash('Simulation not available.', 'error')
            return redirect(url_for('dashboard'))
        
        return render_template('simulation_simple.html', 
                             simulation_type=simulation_type,
                             simulation_data=simulation_data)
    except Exception as e:
        flash(f'Error loading simulation: {e}', 'error')
        logger.error(f"Error loading simulation {simulation_type}: {e}")
        return redirect(url_for('dashboard'))

@app.route('/submit_simulation', methods=['POST'])
@login_required
def submit_simulation():
    """
    Submit simulation responses and calculate results.
    
    Features:
    - Response evaluation
    - Learning feedback
    - Score calculation
    - Progress tracking
    
    Returns:
        str: JSON response with results
    """
    try:
        simulation_type = request.form.get('simulation_type')
        responses = request.form.get('responses', '{}')
        
        # Parse responses
        try:
            responses = json.loads(responses)
        except json.JSONDecodeError:
            responses = {}
        
        # Evaluate simulation
        result = simulation_service.evaluate_simulation(
            current_user.id, 
            simulation_type, 
            responses
        )
        
        if result:
            flash('Simulation completed successfully!', 'success')
            return jsonify({
                'success': True,
                'score': result.score,
                'feedback': result.feedback
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to evaluate simulation'
            })
            
    except Exception as e:
        logger.error(f"Error submitting simulation: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

# =============================================================================
# 10.5 PROGRESS AND ANALYTICS ROUTES
# =============================================================================

@app.route('/profile')
@login_required
def profile():
    """
    User profile route - displays and manages user profile information.
    
    Features:
    - Profile information display
    - Edit capabilities
    - Progress overview
    - Achievement tracking
    
    Returns:
        str: Rendered profile template
    """
    try:
        return render_template('profile.html', user=current_user)
    except Exception as e:
        flash(f'Error loading profile: {e}', 'error')
        logger.error(f"Error loading profile: {e}")
        return redirect(url_for('dashboard'))

@app.route('/update_progress', methods=['POST'])
@login_required
def update_progress():
    """
    Update user progress for modules and activities.
    
    Features:
    - Progress tracking
    - Time spent calculation
    - Status updates
    - Completion validation
    
    Returns:
        str: JSON response with update status
    """
    try:
        module_id = request.form.get('module_id', type=int)
        status = request.form.get('status', 'in_progress')
        score = request.form.get('score', 0, type=int)
        time_spent = request.form.get('time_spent', 0, type=int)
        
        if not module_id:
            return jsonify({'success': False, 'error': 'Module ID required'})
        
        # Get or create progress record
        progress = UserProgress.get_module_progress(current_user.id, module_id)
        if not progress:
            progress = UserProgress(
                user_id=current_user.id,
                module_id=module_id,
                status='not_started'
            )
        
        # Update progress
        progress.status = status
        progress.score = score
        progress.time_spent = time_spent
        
        if progress.save():
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to save progress'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# =============================================================================
# 10.6 SYSTEM ROUTES
# =============================================================================

@app.route('/health')
def health_check():
    """
    Health check endpoint for monitoring and deployment verification.
    
    Features:
    - Database connectivity check
    - Application status
    - Version information
    - Timestamp for monitoring
    
    Returns:
        str: JSON response with health status
    """
    try:
        # Check database connection
        db.session.execute(text('SELECT 1'))
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected',
            'version': '1.0.0'
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 500

# =============================================================================
# 11. ERROR HANDLERS
# =============================================================================

@app.errorhandler(404)
def not_found_error(error):
    """
    Handle 404 Not Found errors.
    
    Args:
        error: The 404 error object
        
    Returns:
        str: Rendered 404 error page
    """
    logger.warning(f"404 error: {error}")
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """
    Handle 500 Internal Server errors.
    
    Features:
    - Database rollback on errors
    - Error logging
    - User-friendly error page
    
    Args:
        error: The 500 error object
        
    Returns:
        str: Rendered 500 error page
    """
    db.session.rollback()
    logger.error(f"500 error: {error}")
    return render_template('500.html'), 500

# =============================================================================
# 12. APPLICATION ENTRY POINT
# =============================================================================

if __name__ == '__main__':
    """
    Main application entry point.
    
    This section:
    - Initializes the application
    - Sets up logging
    - Configures the server
    - Starts the Flask development server
    
    For production deployment, use Gunicorn with the Procfile.
    """
    logger.info("[STARTUP] Initializing Social Engineering Awareness Program with OOP...")
    
    try:
        # Get configuration
        port = int(os.environ.get('PORT', 5000))
        debug = os.environ.get('FLASK_ENV') == 'development'
        
        # Log startup information
        logger.info(f"[SUCCESS] Application ready on port {port}")
        logger.info(f"[INFO] Debug mode: {debug}")
        logger.info(f"[INFO] Access the application at: http://localhost:{port}")
        logger.info(f"[INFO] Default admin credentials: {app.config.get('DEFAULT_ADMIN_USERNAME')} / {app.config.get('DEFAULT_ADMIN_PASSWORD')}")
        logger.info(f"[INFO] Health check available at: http://localhost:{port}/health")
        
        # Start the application
        app.run(debug=debug, host='0.0.0.0', port=port)
        
    except Exception as e:
        logger.error(f"[ERROR] Failed to start application: {e}")
        sys.exit(1) 
