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
from data_models.content_models import Lesson, Reflection, Reference
from data_models.progress_models import Quiz, QuizQuestion, TopicProgress
from data_models.progress_models import AuditLog
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
    raw_level = os.environ.get('LOG_LEVEL', 'INFO')
    log_level = (raw_level or 'INFO').strip().upper()
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
    # Fallback to INFO if an invalid level is provided
    if not hasattr(logging, log_level):
        log_level = 'INFO'
    root_logger.setLevel(getattr(logging, log_level))
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

# Load environment-based configuration (sanitize env var)
_raw_env = os.environ.get('FLASK_ENV', 'production')
config_name = (_raw_env or 'production').strip().lower()
# Fallback safely even if an unexpected value sneaks in
app.config.from_object(config.get(config_name, config['production']))

# Configure reverse proxy for production deployment (Render/Heroku)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure URL building for production
if os.environ.get('RENDER'):
    app.config['SERVER_NAME'] = None  # Allow URL building without server name
    app.config['PREFERRED_URL_SCHEME'] = 'https'

# =============================================================================
# 4. EXTENSIONS AND SERVICES INITIALIZATION
# =============================================================================

# Initialize database
db.init_app(app)

# Ensure schema compatibility at startup (handles Postgres deployments)
with app.app_context():
    try:
        # Create tables if not exist
        db.create_all()
        # Try to widen password_hash column if it's too small (Postgres only)
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        if inspector.has_table('user'):
            backend = db.engine.url.get_backend_name()
            # Postgres migrations
            if backend in ['postgresql', 'postgres']:
                try:
                    db.session.execute(text(
                        "ALTER TABLE \"user\" ALTER COLUMN password_hash TYPE VARCHAR(255)"
                    ))
                    # Ensure is_admin column exists
                    db.session.execute(text(
                        "ALTER TABLE \"user\" ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE"
                    ))
                    db.session.commit()
                except Exception:
                    db.session.rollback()
            # SQLite migrations
            elif backend in ['sqlite']:
                try:
                    # SQLite allows simple ADD COLUMN without IF NOT EXISTS
                    db.session.execute(text(
                        "ALTER TABLE \"user\" ADD COLUMN is_admin BOOLEAN DEFAULT 0"
                    ))
                    db.session.commit()
                except Exception:
                    db.session.rollback()
    except Exception:
        pass

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

        # Ensure admin user has correct credentials (always update on startup)
        if admin_user:
            try:
                # Update admin credentials to ensure they're correct
                admin_user.email = app.config.get('DEFAULT_ADMIN_EMAIL', 'admin@mmdc.edu.ph')
                admin_user.full_name = 'System Administrator'
                admin_user.specialization = 'Information Technology'
                admin_user.year_level = '4th Year'
                
                # Set password from environment or default
                desired_pw = os.environ.get('ADMIN_PASSWORD', app.config.get('DEFAULT_ADMIN_PASSWORD', 'Admin123!@#2025'))
                admin_user.set_password(desired_pw)
                admin_user.save()
                logger.info("[SUCCESS] Admin user credentials updated (administrator)")
            except Exception as pw_e:
                logger.warning(f"[WARNING] Could not update admin credentials: {pw_e}")
        
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
# 7. EDUCATIONAL CONTENT CREATION FUNCTIONS
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
            Module5Content, FinalAssessmentContent
        )
        
        # Module content classes
        module_classes = [
            Module1Content, Module2Content, Module3Content, Module4Content,
            Module5Content, FinalAssessmentContent
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
            'simulation_type': 'quid_pro_quo'
        },
        {
            'name': 'Phishing Detection and Prevention',
            'description': 'Learn about phishing techniques and prevention',
            'content': 'Phishing is a type of social engineering attack where attackers impersonate legitimate entities...',
            'order': 3,
            'has_simulation': True,
            'simulation_type': 'phishing'
        },
        {
            'name': 'Password Security and Authentication',
            'description': 'Understanding password security and authentication methods',
            'content': 'Password security involves creating strong passwords and using multi-factor authentication...',
            'order': 4,
            'has_simulation': True,
            'simulation_type': 'pretexting'
        },
        {
            'name': 'Social Media Security',
            'description': 'Protecting yourself from social engineering attacks on social media',
            'content': 'Social media platforms are common targets for social engineering attacks...',
            'order': 5,
            'has_simulation': True,
            'simulation_type': 'baiting'
        },
        {
            'name': 'Final Assessment - Comprehensive Social Engineering Awareness',
            'description': 'Comprehensive assessment covering all aspects of social engineering awareness and prevention',
            'content': 'This final assessment will test your comprehensive understanding of social engineering awareness...',
            'order': 6,
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
            Module5Questions, FinalAssessmentQuestions
        )
        
        # Question classes mapping
        question_classes = [
            Module1Questions, Module2Questions, Module3Questions, Module4Questions,
            Module5Questions, FinalAssessmentQuestions
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
    - Automatic database initialization
    
    Methods:
        GET: Display registration form
        POST: Process registration data
        
    Returns:
        str: Rendered template or redirect
    """
    # Ensure database is initialized before processing registration
    try:
        with app.app_context():
            db.create_all()
            if Module.count() == 0:
                create_default_data()
                logger.info("[SUCCESS] Database auto-initialized during registration")
    except Exception as e:
        logger.error(f"[ERROR] Auto-database init during registration failed: {e}")
    
    if request.method == 'POST':
        try:
            # Get and validate form data
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            specialization = request.form.get('specialization', '')
            year_level = request.form.get('year_level', '')
            
            # Set default full name (can be updated in profile later)
            full_name = f"User {username}"
            
            # Validate required fields
            if not all([username, email, password, confirm_password, specialization, year_level]):
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
    - Automatic database initialization
    
    Methods:
        GET: Display login form
        POST: Process login credentials
        
    Returns:
        str: Rendered template or redirect
    """
    # Ensure database is initialized before processing login
    try:
        with app.app_context():
            db.create_all()
            if Module.count() == 0:
                create_default_data()
                logger.info("[SUCCESS] Database auto-initialized during login")
    except Exception as e:
        logger.error(f"[ERROR] Auto-database init during login failed: {e}")
    
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

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    """
    Forgot password route - handles password reset requests.
    
    Features:
    - Email-based password reset
    - Token generation and validation
    - Security measures for reset process
    
    Returns:
        str: Rendered template or redirect
    """
    if request.method == 'POST':
        try:
            email = request.form.get('email')
            if not email:
                flash('Please enter your email address.', 'error')
                return render_template('forgot_password.html')
            
            user = User.get_by_email(email)
            if user:
                # Generate reset token
                token = secrets.token_urlsafe(32)
                reset_token = PasswordResetToken(
                    user_id=user.id,
                    token=token,
                    expires_at=datetime.now() + timedelta(hours=24)
                )
                reset_token.save()
                
                # In a real application, send email here
                # For now, just show a success message
                flash('Password reset instructions have been sent to your email.', 'success')
                logger.info(f"Password reset requested for user {user.username}")
            else:
                # Don't reveal if email exists or not for security
                flash('If the email exists, password reset instructions have been sent.', 'info')
            
            return redirect(url_for('login'))
            
        except Exception as e:
            flash('An error occurred. Please try again.', 'error')
            logger.error(f"Password reset error: {e}")
    
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """
    Reset password route - handles password reset with token.
    
    Features:
    - Token validation
    - Password strength validation
    - Secure password update
    
    Args:
        token: Password reset token
        
    Returns:
        str: Rendered template or redirect
    """
    try:
        # Find valid reset token
        reset_token = PasswordResetToken.query.filter(
            PasswordResetToken.token == token,
            PasswordResetToken.expires_at > datetime.now(),
            PasswordResetToken.used == False
        ).first()
        
        if not reset_token:
            flash('Invalid or expired reset token.', 'error')
            return redirect(url_for('login'))
        
        if request.method == 'POST':
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            
            if not password or not confirm_password:
                flash('Please fill in all fields.', 'error')
            elif password != confirm_password:
                flash('Passwords do not match.', 'error')
            elif len(password) < 12:
                flash('Password must be at least 12 characters long.', 'error')
            else:
                # Update user password
                user = User.get_by_id(reset_token.user_id)
                if user:
                    user.set_password(password)
                    user.save()
                    
                    # Mark token as used
                    reset_token.used = True
                    reset_token.save()
                    
                    flash('Password has been reset successfully. Please log in.', 'success')
                    logger.info(f"Password reset completed for user {user.username}")
                    return redirect(url_for('login'))
        
        return render_template('reset_password.html', token=token)
        
    except Exception as e:
        flash('An error occurred. Please try again.', 'error')
        logger.error(f"Password reset error: {e}")
        return redirect(url_for('login'))

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
        total_modules = Module.count() if modules else 0
        
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
            percent = int((ar.score / ar.total_questions) * 100) if ar.total_questions and ar.total_questions > 0 else ar.score
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
            average_score = int((total_score / total_questions) * 100) if total_questions and total_questions > 0 else 0
        else:
            average_score = 0
        
        # Calculate total time spent (estimate: 30 minutes per completed module)
        total_time_spent = completed_modules * 30
        
        # Ensure all variables are safe for template rendering
        safe_user_stats = user_stats or {}
        safe_user_progress = user_progress or []
        safe_modules = modules or []
        safe_recent_activities = recent_activities or []
        
        return render_template('dashboard.html', 
                             user_stats=safe_user_stats,
                             user_progress=safe_user_progress,
                             modules=safe_modules,
                             completed_modules=completed_modules,
                             completed_module_ids=completed_module_ids,
                             total_modules=total_modules,
                             final_result=final_result,
                             survey_completed=survey_completed,
                             accessible_modules=accessible_modules,
                             recent_activities=safe_recent_activities,
                             average_score=average_score,
                             total_time_spent=total_time_spent)
    except Exception as e:
        flash(f'Error loading dashboard: {e}', 'error')
        logger.error(f"Error loading dashboard: {e}")
        # Return a minimal dashboard with safe defaults
        try:
            return render_template('dashboard.html', 
                                 user_stats={},
                                 user_progress=[],
                                 modules=[],
                                 completed_modules=0,
                                 completed_module_ids=[],
                                 total_modules=0,
                                 final_result=None,
                                 survey_completed=None,
                                 accessible_modules=[],
                                 recent_activities=[],
                                 average_score=0,
                                 total_time_spent=0)
        except Exception as template_error:
            logger.error(f"Template rendering error: {template_error}")
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
        
        # Load DB-backed lessons for this module (if any)
        try:
            lessons = Lesson.query.filter_by(module_id=module_id).order_by(Lesson.order.asc()).all()
            if lessons is None:
                lessons = []
        except Exception as e:
            logger.warning(f"Failed to load lessons for module {module_id}: {e}")
            lessons = []

        # Load Reflection and References
        try:
            reflection = Reflection.query.filter_by(module_id=module_id).first()
        except Exception as e:
            logger.warning(f"Failed to load reflection for module {module_id}: {e}")
            reflection = None
        try:
            references = Reference.query.filter_by(module_id=module_id).order_by(Reference.order.asc()).all()
            if references is None:
                references = []
        except Exception as e:
            logger.warning(f"Failed to load references for module {module_id}: {e}")
            references = []

        # Get knowledge check score for this module
        knowledge_check_result = AssessmentResult.query.filter_by(
            user_id=current_user.id,
            module_id=module_id,
            assessment_type='knowledge_check'
        ).order_by(AssessmentResult.created_at.desc()).first()
        
        # Calculate percentage score
        if knowledge_check_result and knowledge_check_result.total_questions and knowledge_check_result.total_questions > 0:
            knowledge_check_score = int((knowledge_check_result.score / knowledge_check_result.total_questions) * 100)
        else:
            knowledge_check_score = 0
        
        # Compute topic completion percentage for sidebar and completed topic ids
        total_topics = 0
        try:
            total_topics = sum(len(getattr(l, 'topics', []) or []) for l in (lessons or []))
        except Exception:
            total_topics = 0
        completed_topics = 0
        completed_topic_ids = set()
        if current_user.is_authenticated and total_topics > 0:
            try:
                tps = TopicProgress.query.filter_by(user_id=current_user.id, module_id=module_id, is_completed=True).all()
                completed_topics = len(tps)
                completed_topic_ids = {tp.topic_id for tp in (tps or [])}
            except Exception as e:
                logger.warning(f"Failed to load topic progress for user {current_user.id} module {module_id}: {e}")
                completed_topics = 0
                completed_topic_ids = set()
        topics_completion_pct = int((completed_topics / total_topics) * 100) if total_topics else 0

        # Determine first incomplete topic id for "Continue" button
        first_incomplete_topic_id = None
        try:
            for l in (lessons or []):
                for t in getattr(l, 'topics', []) or []:
                    if getattr(t, 'id', None) not in completed_topic_ids:
                        first_incomplete_topic_id = t.id
                        break
                if first_incomplete_topic_id:
                    break
        except Exception:
            first_incomplete_topic_id = None

        return render_template('module.html', 
                             module=module_obj,
                             progress=progress,
                             lessons=lessons,
                             reflection=reflection,
                             references=references,
                             knowledge_check_score=knowledge_check_score,
                             topics_completion_pct=topics_completion_pct,
                             completed_topics=completed_topics,
                             total_topics=total_topics,
                             completed_topic_ids=completed_topic_ids,
                             first_incomplete_topic_id=first_incomplete_topic_id)
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
        try:
            all_questions = KnowledgeCheckQuestion.query.filter_by(module_id=module_id).all()
        except Exception as e:
            logger.error(f"Error loading questions for module {module_id}: {e}")
            all_questions = []
        if not all_questions:
            flash('No questions available for this module.', 'error')
            return redirect(url_for('module', module_id=module_id))
        
        # Pick a randomized subset each attempt
        desired_count = app.config.get('KNOWLEDGE_CHECK_NUM_QUESTIONS', 5)
        if len(all_questions) > desired_count and desired_count > 0:
            questions = random.sample(all_questions, desired_count)
        else:
            questions = list(all_questions)
            random.shuffle(questions)

        # Persist the exact questions for this attempt so submission grades correctly
        try:
            session[f'kc_qids_{module_id}'] = [q.id for q in questions]
        except Exception:
            # If session storage fails, continue; submit will fall back to all questions
            pass
        
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
        
        # Get only the questions presented to the user in this attempt
        qids_key = f'kc_qids_{module_id}'
        qids = None
        try:
            qids = session.get(qids_key)
        except Exception:
            qids = None

        if qids:
            try:
                questions = KnowledgeCheckQuestion.query.filter(
                    KnowledgeCheckQuestion.id.in_(qids)
                ).all()
                # Preserve original order from qids
                qpos = {qid: idx for idx, qid in enumerate(qids)}
                questions.sort(key=lambda q: qpos.get(q.id, 1_000_000))
            except Exception:
                questions = KnowledgeCheckQuestion.query.filter_by(module_id=module_id).all()
        else:
            # Fallback: all questions (older sessions)
            questions = KnowledgeCheckQuestion.query.filter_by(module_id=module_id).all()
        if not questions:
            flash('No questions available for this module.', 'error')
            return redirect(url_for('module', module_id=module_id))
        
        # Process answers and build detailed feedback per question
        answers = {}
        correct_answers = 0
        total_questions = len(questions)
        detailed_results = []
        
        for question in questions:
            answer = request.form.get(f'question_{question.id}')
            answers[question.id] = answer
            
            is_correct = (answer == question.correct_answer)
            if is_correct:
                correct_answers += 1
            
            # Prefer question.explanation when available; otherwise create a simple message
            try:
                base_expl = getattr(question, 'explanation', None)
            except Exception:
                base_expl = None
            if not base_expl:
                base_expl = 'Review the lesson content to understand why this is the correct answer.'
            explanation = ("Correct: " + base_expl) if is_correct else ("Incorrect: " + base_expl)
            
            detailed_results.append({
                'question_text': getattr(question, 'question_text', ''),
                'user_answer': (answer or ''),
                'correct_answer': getattr(question, 'correct_answer', ''),
                'is_correct': is_correct,
                'explanation': explanation
            })
        
        # Calculate score
        score = correct_answers
        percentage = int((correct_answers / total_questions) * 100) if total_questions and total_questions > 0 else 0
        
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
            
            # Limit review to the last 5 answered questions
            review_items = detailed_results[-5:] if detailed_results else []

            # Clear the stored question ids after grading
            try:
                session.pop(qids_key, None)
            except Exception:
                pass

            return render_template('assessment_result.html',
                                     module=module_obj,
                                     score=correct_answers,
                                     total_questions=total_questions,
                                     correct_answers=correct_answers,
                                     percentage=percentage,
                                     passed=passed,
                                     detailed_results=review_items,
                                     questions=questions,
                                     answers=answers,
                                     module_id=module_id)
        else:
            flash('Error saving assessment results.', 'error')
            return redirect(url_for('module', module_id=module_id))
        
    except Exception as e:
        flash(f'Error submitting assessment: {e}', 'error')
        logger.error(f"Error submitting assessment for module {module_id}: {e}")
        return redirect(url_for('dashboard'))

# =============================================================================
# 10.4 FINAL ASSESSMENT ROUTES
# =============================================================================

@app.route('/final_assessment')
@login_required
def final_assessment():
    """
    Final assessment route - displays the comprehensive final assessment.
    
    Features:
    - Access control (only after completing all modules)
    - Comprehensive question set
    - Time tracking
    - Certificate eligibility
    
    Returns:
        str: Rendered final assessment template or redirect
    """
    try:
        # Check if user has completed all modules
        completed_modules = len(user_service.get_user_completed_modules(current_user.id))
        total_modules = Module.count()
        
        if completed_modules < total_modules:
            flash('You must complete all modules before taking the Final Assessment.', 'warning')
            return redirect(url_for('dashboard'))
        
        # Check if user has already passed
        existing_result = AssessmentResult.query.filter_by(
            user_id=current_user.id, 
            assessment_type='final_assessment',
            passed=True
        ).first()
        
        if existing_result:
            flash('You have already passed the Final Assessment!', 'info')
            return redirect(url_for('dashboard'))
        
        return render_template('final_assessment_simple.html')
        
    except Exception as e:
        flash(f'Error loading final assessment: {e}', 'error')
        logger.error(f"Error loading final assessment: {e}")
        return redirect(url_for('dashboard'))

@app.route('/final_assessment_questions')
@login_required
def final_assessment_questions():
    """
    Final assessment questions route - displays the actual assessment.
    
    Returns:
        str: Rendered final assessment questions template
    """
    try:
        # Get final assessment questions
        questions = FinalAssessmentQuestion.query.all()
        if not questions:
            flash('No final assessment questions available.', 'error')
            return redirect(url_for('dashboard'))
        
        # Shuffle questions for variety
        random.shuffle(questions)
        
        return render_template('final_assessment_questions.html', questions=questions)
        
    except Exception as e:
        flash(f'Error loading final assessment questions: {e}', 'error')
        logger.error(f"Error loading final assessment questions: {e}")
        return redirect(url_for('dashboard'))

@app.route('/submit_final_assessment', methods=['POST'])
@login_required
def submit_final_assessment():
    """
    Submit final assessment answers and calculate results.
    
    Returns:
        str: Rendered result template or redirect
    """
    try:
        # Get questions
        questions = FinalAssessmentQuestion.query.all()
        if not questions:
            flash('No final assessment questions available.', 'error')
            return redirect(url_for('dashboard'))
        
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
        percentage = int((correct_answers / total_questions) * 100) if total_questions and total_questions > 0 else 0
        
        # Determine if passed (70% threshold for final assessment)
        passed = percentage >= app.config.get('FINAL_ASSESSMENT_PASSING_SCORE', 70)
        
        # Create assessment result
        result = AssessmentResult(
            user_id=current_user.id,
            module_id=None,  # Final assessment is not tied to a specific module
            assessment_type='final_assessment',
            score=score,
            total_questions=total_questions,
            correct_answers=correct_answers,
            passed=passed
        )
        
        if result.save():
            flash(f'Final Assessment completed! Score: {percentage}%', 'success' if passed else 'warning')
            logger.info(f"User {current_user.username} completed final assessment with score {percentage}%")
            
            return render_template('final_assessment_result.html',
                                     score=percentage,
                                     total_questions=total_questions,
                                     correct_answers=correct_answers,
                                     passed=passed,
                                     questions=questions,
                                     answers=answers)
        else:
            flash('Error saving final assessment results.', 'error')
            return redirect(url_for('final_assessment'))
        
    except Exception as e:
        flash(f'Error submitting final assessment: {e}', 'error')
        logger.error(f"Error submitting final assessment: {e}")
        return redirect(url_for('dashboard'))

# =============================================================================
# 10.5 SURVEY AND CERTIFICATE ROUTES
# =============================================================================

@app.route('/survey')
@login_required
def survey():
    """
    Program survey route - displays feedback survey.
    
    Returns:
        str: Rendered survey template
    """
    try:
        # Check if user has passed final assessment
        final_result = AssessmentResult.query.filter_by(
            user_id=current_user.id,
            assessment_type='final_assessment',
            passed=True
        ).first()
        
        if not final_result:
            flash('You must pass the Final Assessment before taking the survey.', 'warning')
            return redirect(url_for('dashboard'))
        
        # Check if survey already completed
        existing_survey = FeedbackSurvey.query.filter_by(user_id=current_user.id).first()
        if existing_survey:
            flash('You have already completed the survey.', 'info')
            return redirect(url_for('dashboard'))
        
        return render_template('survey.html')
        
    except Exception as e:
        flash(f'Error loading survey: {e}', 'error')
        logger.error(f"Error loading survey: {e}")
        return redirect(url_for('dashboard'))

@app.route('/submit_survey', methods=['POST'])
@login_required
def submit_survey():
    """
    Submit survey responses.
    
    Returns:
        str: Redirect to certificate or dashboard
    """
    try:
        # Get survey data
        rating = request.form.get('rating', type=int)
        feedback = request.form.get('feedback', '')
        
        # Create survey record
        survey = FeedbackSurvey(
            user_id=current_user.id,
            rating=rating,
            feedback=feedback
        )
        
        if survey.save():
            flash('Survey submitted successfully!', 'success')
            logger.info(f"User {current_user.username} completed survey")
            return redirect(url_for('certificate'))
        else:
            flash('Error saving survey.', 'error')
            return redirect(url_for('survey'))
        
    except Exception as e:
        flash(f'Error submitting survey: {e}', 'error')
        logger.error(f"Error submitting survey: {e}")
        return redirect(url_for('survey'))

@app.route('/certificate')
@login_required
def certificate():
    """
    Certificate generation route.
    
    Returns:
        str: Rendered certificate template
    """
    try:
        # Check if user is eligible for certificate
        final_result = AssessmentResult.query.filter_by(
            user_id=current_user.id,
            assessment_type='final_assessment',
            passed=True
        ).first()
        
        survey_completed = FeedbackSurvey.query.filter_by(user_id=current_user.id).first()
        
        if not final_result:
            flash('You must pass the Final Assessment to generate a certificate.', 'warning')
            return redirect(url_for('dashboard'))
        
        if not survey_completed:
            flash('You must complete the survey to generate a certificate.', 'warning')
            return redirect(url_for('survey'))
        
        return render_template('certificate.html', user=current_user)
        
    except Exception as e:
        flash(f'Error generating certificate: {e}', 'error')
        logger.error(f"Error generating certificate: {e}")
        return redirect(url_for('dashboard'))

# =============================================================================
# 10.6 SIMULATION ROUTES
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
# 10.7 PROGRESS AND ANALYTICS ROUTES
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
        # Accept both JSON and form payloads
        payload = None
        if request.is_json:
            payload = request.get_json(silent=True) or {}
        
        if payload:
            module_id = payload.get('module_id')
            status = payload.get('status', 'in_progress')
            score = payload.get('score', 0)
            time_spent = payload.get('time_spent', 0)
            topic_id = payload.get('topic_id')
            completed_flag = payload.get('completed', 'true')
        else:
            module_id = request.form.get('module_id', type=int)
            status = request.form.get('status', 'in_progress')
            score = request.form.get('score', 0, type=int)
            time_spent = request.form.get('time_spent', 0, type=int)
            topic_id = request.form.get('topic_id', type=int)
            completed_flag = request.form.get('completed', default='true')

        if not module_id:
            return jsonify({'success': False, 'error': 'Module ID required'}), 400

        # Topic-level toggle
        if topic_id:
            try:
                tp = TopicProgress.query.filter_by(user_id=current_user.id, topic_id=topic_id, module_id=module_id).first()
                if not tp:
                    tp = TopicProgress(user_id=current_user.id, topic_id=topic_id, module_id=module_id)
                    db.session.add(tp)
                mark_completed = (str(completed_flag).lower() != 'false')
                tp.is_completed = mark_completed
                tp.completed_at = datetime.utcnow() if mark_completed else None
                db.session.commit()
                return jsonify({'success': True, 'topic_id': topic_id, 'completed': tp.is_completed})
            except Exception as e:
                db.session.rollback()
                logger.error(f"Failed to update topic progress: {e}")
                return jsonify({'success': False, 'error': 'Failed to update topic progress'}), 500

        # Module-level progress
        progress = UserProgress.get_module_progress(current_user.id, module_id)
        if not progress:
            progress = UserProgress(
                user_id=current_user.id,
                module_id=module_id,
                status='not_started'
            )

        progress.status = status
        progress.score = score
        progress.time_spent = time_spent

        if progress.save():
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to save progress'}), 500

    except Exception as e:
        logger.error(f"update_progress failed: {e}")
        return jsonify({'success': False, 'error': 'Unexpected server error'}), 500

# =============================================================================
# 10.8 SYSTEM ROUTES
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

@app.route('/init-db')
def init_database_route():
    """
    Database initialization endpoint for Render deployment.
    
    This endpoint ensures the database is properly initialized
    when the application starts on Render.
    
    Returns:
        str: JSON response with initialization status
    """
    try:
        with app.app_context():
            init_database()
        return jsonify({
            'status': 'success',
            'message': 'Database initialized successfully',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
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
# 12. ADMIN DASHBOARD ROUTES
# =============================================================================

def admin_required(f):
    """Decorator to require admin access"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please login to access admin panel.', 'error')
            return redirect(url_for('login'))
        
        # Check if user is admin
        if getattr(current_user, 'is_admin', False) is not True and current_user.username != 'administrator':
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    """Admin dashboard main page"""
    try:
        # Get system statistics
        total_users = User.count()
        total_modules = Module.query.filter(Module.id <= 5).count()  # Only count active modules (1-5)
        total_assessments = AssessmentResult.count()
        total_simulations = SimulationResult.count()
        
        # Get recent activity
        recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
        recent_assessments = AssessmentResult.query.order_by(AssessmentResult.created_at.desc()).limit(10).all()
        
        # Get user statistics
        users_by_specialization = db.session.query(
            User.specialization, 
            db.func.count(User.id)
        ).group_by(User.specialization).all()
        
        users_by_year = db.session.query(
            User.year_level,
            db.func.count(User.id)
        ).group_by(User.year_level).all()
        
        return render_template('admin/dashboard.html',
                             total_users=total_users,
                             total_modules=total_modules,
                             total_assessments=total_assessments,
                             total_simulations=total_simulations,
                             recent_users=recent_users,
                             recent_assessments=recent_assessments,
                             users_by_specialization=users_by_specialization,
                             users_by_year=users_by_year)
        
    except Exception as e:
        flash(f'Error loading admin dashboard: {e}', 'error')
        logger.error(f"Error loading admin dashboard: {e}")
        return redirect(url_for('dashboard'))

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    """User management page"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        # Optional search filters
        query = User.query
        search = request.args.get('search', '').strip()
        specialization = request.args.get('specialization', '').strip()
        year_level = request.args.get('year_level', '').strip()
        
        if search:
            like = f"%{search}%"
            query = query.filter(db.or_(
                User.full_name.ilike(like),
                User.username.ilike(like),
                User.email.ilike(like)
            ))
        if specialization:
            query = query.filter_by(specialization=specialization)
        if year_level:
            query = query.filter_by(year_level=year_level)
        
        users = query.order_by(User.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('admin/users.html', users=users)
        
    except Exception as e:
        flash(f'Error loading users: {e}', 'error')
        logger.error(f"Error loading users: {e}")
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_create_user():
    """Create a new user (and optionally make admin)"""
    try:
        if request.method == 'POST':
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            full_name = request.form.get('full_name', '').strip() or f"User {username}"
            specialization = request.form.get('specialization', '').strip()
            year_level = request.form.get('year_level', '').strip()
            is_admin_flag = request.form.get('is_admin') == 'on'

            user_data = {
                'username': username,
                'email': email,
                'password': password,
                'full_name': full_name,
                'specialization': specialization,
                'year_level': year_level
            }
            try:
                new_user = user_service.create_user(user_data)
                if new_user and is_admin_flag:
                    try:
                        new_user.is_admin = True
                        new_user.save()
                    except Exception:
                        pass
                flash('User created successfully.', 'success')
                return redirect(url_for('admin_users'))
            except ValueError as ve:
                flash(str(ve), 'error')
        
        return render_template('admin/create_user.html')
    except Exception as e:
        flash(f'Error creating user: {e}', 'error')
        logger.error(f"Error creating user: {e}")
        return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:user_id>')
@login_required
@admin_required
def admin_user_detail(user_id):
    """User detail page"""
    try:
        user = User.get_by_id(user_id)
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('admin_users'))
        
        # Get user progress
        progress = UserProgress.get_user_progress(user_id)
        assessments = AssessmentResult.query.filter_by(user_id=user_id).all()
        simulations = SimulationResult.query.filter_by(user_id=user_id).all()
        audit_logs = []
        try:
            if getattr(user, 'is_admin', False) or user.username == 'administrator':
                audit_logs = AuditLog.recent_for_user(user_id, limit=20)
        except Exception:
            audit_logs = []
        
        return render_template('admin/user_detail.html',
                             user=user,
                             progress=progress,
                             assessments=assessments,
                             simulations=simulations,
                             audit_logs=audit_logs)
        
    except Exception as e:
        flash(f'Error loading user details: {e}', 'error')
        logger.error(f"Error loading user details: {e}")
        return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_user(user_id):
    """Edit user information"""
    try:
        user = User.get_by_id(user_id)
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('admin_users'))
        
        if request.method == 'POST':
            # Update user information
            user.full_name = request.form.get('full_name', user.full_name)
            user.email = request.form.get('email', user.email)
            user.specialization = request.form.get('specialization', user.specialization)
            user.year_level = request.form.get('year_level', user.year_level)
            user.address = request.form.get('address', user.address)
            
            # Toggle admin if checkbox provided
            is_admin_flag = request.form.get('is_admin') == 'on'
            try:
                user.is_admin = is_admin_flag if user.username != 'administrator' else True
            except Exception:
                pass
            
            if user.save():
                flash('User updated successfully!', 'success')
                return redirect(url_for('admin_user_detail', user_id=user_id))
            else:
                flash('Error updating user.', 'error')
        
        return render_template('admin/edit_user.html', user=user)
        
    except Exception as e:
        flash(f'Error editing user: {e}', 'error')
        logger.error(f"Error editing user: {e}")
        return redirect(url_for('admin_users'))

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    """Delete user"""
    try:
        user = User.get_by_id(user_id)
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('admin_users'))
        
        if user.username == 'administrator':
            flash('Cannot delete administrator account.', 'error')
            return redirect(url_for('admin_users'))
        
        if user.delete():
            flash('User deleted successfully!', 'success')
        else:
            flash('Error deleting user.', 'error')
        
        return redirect(url_for('admin_users'))
        
    except Exception as e:
        flash(f'Error deleting user: {e}', 'error')
        logger.error(f"Error deleting user: {e}")
        return redirect(url_for('admin_users'))

@app.route('/admin/modules')
@login_required
@admin_required
def admin_modules():
    """Module management page"""
    try:
        # Get only the first 5 modules (our active modules)
        modules = Module.query.filter(Module.id <= 5).order_by(Module.id).all()
        return render_template('admin/modules.html', modules=modules)
        
    except Exception as e:
        flash(f'Error loading modules: {e}', 'error')
        logger.error(f"Error loading modules: {e}")
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/analytics')
@login_required
@admin_required
def admin_analytics():
    """Analytics and reporting page"""
    try:
        # Get basic system statistics
        total_users = User.count()
        total_modules = Module.count()
        total_assessments = AssessmentResult.count()
        total_simulations = SimulationResult.count()
        
        # Create basic system stats
        system_stats = {
            'total_users': total_users,
            'total_modules': total_modules,
            'total_assessments': total_assessments,
            'total_simulations': total_simulations
        }
        
        # Create basic user performance data
        user_performance = {
            'completion_distribution': {
                'completed_all': 0,
                'completed_half': 0,
                'started': 0,
                'not_started': 0
            },
            'average_scores': {
                'knowledge_check': 0,
                'final_assessment': 0,
                'simulation': 0
            }
        }
        
        # Create basic module analytics
        module_analytics = {}
        
        return render_template('admin/analytics.html',
                             system_stats=system_stats,
                             user_performance=user_performance,
                             module_analytics=module_analytics)
        
    except Exception as e:
        flash(f'Error loading analytics: {e}', 'error')
        logger.error(f"Error loading analytics: {e}")
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/settings')
@login_required
@admin_required
def admin_settings():
    """System settings page"""
    try:
        return render_template('admin/settings.html')
        
    except Exception as e:
        flash(f'Error loading settings: {e}', 'error')
        logger.error(f"Error loading settings: {e}")
        return redirect(url_for('admin_dashboard'))

@app.route('/create-admin')
@login_required
@admin_required
def create_admin():
    """Create admin user if it doesn't exist - DIRECT APPROACH"""
    try:
        # Block in production unless explicitly allowed
        if not app.config.get('ALLOW_ADMIN_MAINTENANCE', False):
            return "❌ This endpoint is disabled. Set ALLOW_ADMIN_MAINTENANCE=true to enable.", 403
        with app.app_context():
            # Ensure database tables exist
            db.create_all()
            
            # Check if admin user already exists
            admin_user = User.query.filter_by(username='administrator').first()
            
            if admin_user:
                # Update existing admin user
                admin_user.email = 'admin@mmdc.edu.ph'
                admin_user.full_name = 'System Administrator'
                admin_user.specialization = 'Information Technology'
                admin_user.year_level = '4th Year'
                admin_user.set_password('Admin123!@#2025')
                admin_user.save()
                return f"✅ Admin user updated successfully<br>Username: administrator<br>Password: Admin123!@#2025<br>Email: admin@mmdc.edu.ph"
            else:
                # Create new admin user
                admin_data = {
                    'username': 'administrator',
                    'email': 'admin@mmdc.edu.ph',
                    'password': 'Admin123!@#2025',
                    'full_name': 'System Administrator',
                    'specialization': 'Information Technology',
                    'year_level': '4th Year'
                }
                
                user = user_service.create_user(admin_data)
                if user:
                    return f"✅ Admin user created successfully<br>Username: administrator<br>Password: Admin123!@#2025<br>Email: admin@mmdc.edu.ph"
                else:
                    return f"❌ Failed to create admin user"
                
    except Exception as e:
        return f"❌ Error: {str(e)}"

@app.route('/create-admin-direct')
@login_required
@admin_required
def create_admin_direct():
    """Create admin user using direct SQLAlchemy - BACKUP METHOD"""
    try:
        # Block in production unless explicitly allowed
        if not app.config.get('ALLOW_ADMIN_MAINTENANCE', False):
            return "❌ This endpoint is disabled. Set ALLOW_ADMIN_MAINTENANCE=true to enable.", 403
        with app.app_context():
            # Ensure database tables exist
            db.create_all()
            
            # Check if admin user already exists
            admin_user = User.query.filter_by(username='administrator').first()
            
            if admin_user:
                # Update existing admin user
                admin_user.email = 'admin@mmdc.edu.ph'
                admin_user.full_name = 'System Administrator'
                admin_user.specialization = 'Information Technology'
                admin_user.year_level = '4th Year'
                admin_user.set_password('Admin123!@#2025')
                db.session.commit()
                return f"✅ Admin user updated successfully (Direct Method)<br>Username: administrator<br>Password: Admin123!@#2025<br>Email: admin@mmdc.edu.ph"
            else:
                # Create new admin user directly
                from werkzeug.security import generate_password_hash
                
                admin_user = User(
                    username='administrator',
                    email='admin@mmdc.edu.ph',
                    password_hash=generate_password_hash('Admin123!@#2025'),
                    full_name='System Administrator',
                    specialization='Information Technology',
                    year_level='4th Year'
                )
                
                db.session.add(admin_user)
                db.session.commit()
                return f"✅ Admin user created successfully (Direct Method)<br>Username: administrator<br>Password: Admin123!@#2025<br>Email: admin@mmdc.edu.ph"
                
    except Exception as e:
        return f"❌ Direct Method Error: {str(e)}"

@app.route('/admin/modules/<int:module_id>/edit')
@login_required
@admin_required
def admin_edit_module(module_id):
    """Edit module content page"""
    try:
        module = Module.get_by_id(module_id)
        if not module:
            flash('Module not found.', 'error')
            return redirect(url_for('admin_modules'))
        
        # Get module content using ModuleManagerService
        from business_services.module_manager_service import ModuleManagerService
        module_manager = ModuleManagerService()
        
        # Get module content
        content = module_manager.get_module_content(module_id)
        questions = module_manager.get_knowledge_check_questions(module_id)
        
        # Ensure content is a dictionary
        if content is None:
            content = {
                'title': module.name,
                'description': module.description,
                'content': 'No content available',
                'learning_objectives': [],
                'estimated_time': 30,
                'difficulty_level': 'intermediate'
            }
        
        return render_template('admin/edit_module.html', 
                             module=module, 
                             content=content, 
                             questions=questions)
        
    except Exception as e:
        flash(f'Error loading module content: {e}', 'error')
        logger.error(f"Error loading module content: {e}")
        return redirect(url_for('admin_modules'))

@app.route('/admin/modules/<int:module_id>/update', methods=['POST'])
@login_required
@admin_required
def admin_update_module(module_id):
    """Update module content"""
    try:
        module = Module.get_by_id(module_id)
        if not module:
            flash('Module not found.', 'error')
            return redirect(url_for('admin_modules'))
        
        # Get form data
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        
        if not title:
            flash('Title is required.', 'error')
            return redirect(url_for('admin_edit_module', module_id=module_id))
        
        # Update module basic info
        module.name = title
        module.description = description
        
        if module.save():
            flash('Module updated successfully!', 'success')
        else:
            flash('Error updating module.', 'error')
        
        return redirect(url_for('admin_edit_module', module_id=module_id))
        
    except Exception as e:
        flash(f'Error updating module: {e}', 'error')
        logger.error(f"Error updating module: {e}")
        return redirect(url_for('admin_modules'))


# =============================================================================
# 13. APPLICATION ENTRY POINT
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
        # Initialize database when app starts (not during import)
        with app.app_context():
            try:
                init_database()
                logger.info("[SUCCESS] Database initialized on startup")
                # Ensure primary admin has is_admin flag locally
                try:
                    admin = User.get_by_username('administrator')
                    if admin and getattr(admin, 'is_admin', False) is not True:
                        admin.is_admin = True
                        admin.save()
                        logger.info("[SUCCESS] Primary admin flagged as is_admin")
                except Exception as _e:
                    logger.warning(f"[WARNING] Unable to flag primary admin: {_e}")
            except Exception as e:
                logger.error(f"[ERROR] Database initialization on startup failed: {e}")
                # Continue anyway - the app might still work
        
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

# =============================================================================
# 13. DATABASE INITIALIZATION FOR PRODUCTION
# =============================================================================

# Simple database initialization that works with Flask 3.0
# This runs when the module is imported but after all functions are defined
try:
    with app.app_context():
        # Always try to create tables first, then check if data exists
        db.create_all()
        logger.info("[SUCCESS] Database tables created")
        
        # Only populate data if database is empty
        if Module.count() == 0:
            create_default_data()
            logger.info("[SUCCESS] Database initialized on import (production)")
        else:
            logger.info("[SUCCESS] Database already has data")
except Exception as e:
    logger.error(f"[ERROR] Production database init failed: {e}")
    # Continue anyway - the app will work and can be initialized via /init-db endpoint 
