from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.security import remember, forget
from .models import DBSession, Habit, User, HabitProgress
from datetime import datetime, timedelta
from sqlalchemy import func

@view_config(route_name='welcome', renderer='templates/welcome.jinja2')
def welcome_view(request):
    user_id = request.authenticated_userid
    if user_id:
        return HTTPFound(location=request.route_url('home'))
    return {}

@view_config(route_name='home', renderer='home.jinja2')
def home_view(request):
    user_id = request.authenticated_userid

    print(f"DEBUG - user_id: {user_id}")

    if not user_id:
        return HTTPFound(location=request.route_url('login'))

    habits = request.dbsession.query(Habit).filter_by(user_id=user_id).all()

    print(f"DEBUG - habits count: {len(habits)}")

    progress_today = {}
    today = datetime.utcnow().date()

    for habit in habits:
        count = request.dbsession.query(HabitProgress).filter(
            HabitProgress.habit_id == habit.id,
            HabitProgress.date >= datetime.combine(today, datetime.min.time()),
            HabitProgress.date <= datetime.combine(today, datetime.max.time())
        ).count()

        progress_today[habit.id] = (count > 0)

    return {
        'habits': habits,
        'progress_today': progress_today
    }
    
@view_config(route_name='register', renderer='templates/register.jinja2', request_method=['GET', 'POST'])
def register_view(request):
    if request.method == 'POST':
        name = request.params.get('name')
        email = request.params.get('email')
        password = request.params.get('password')

        if not (name and email and password):
            return {'error': 'Todos los campos son requeridos.', 'name': name, 'email': email}

        existing = DBSession.query(User).filter_by(email=email).first()
        if existing:
            return {'error': 'El correo ya está registrado.', 'name': name, 'email': email}

        # Sin bcrypt, contraseña en texto plano (no recomendado)
        user = User(name=name, email=email, password=password)
        DBSession.add(user)
        DBSession.commit()

        headers = remember(request, user.id)
        return HTTPFound(location=request.route_url('home'), headers=headers)

    return {}

@view_config(route_name='login', renderer='templates/login.jinja2', request_method=['GET', 'POST'])
def login_view(request):
    if request.method == 'POST':
        email = request.params.get('email')
        password = request.params.get('password')

        if not email or not password:
            return {'error': 'Por favor ingresa email y contraseña'}

        user = DBSession.query(User).filter_by(email=email).first()

        if user is None:
            return {'error': 'Usuario no encontrado'}

        # Comparación sencilla sin bcrypt (NO RECOMENDADO para producción)
        if user.password == password:
            headers = remember(request, user.id)
            return HTTPFound(location=request.route_url('home'), headers=headers)
        else:
            return {'error': 'Contraseña incorrecta'}

    return {}

@view_config(route_name='logout')
def logout_view(request):
    headers = forget(request)
    return HTTPFound(location=request.route_url('welcome'), headers=headers)

@view_config(route_name='add_habit', renderer='add_habit.jinja2', request_method=['GET', 'POST'])
def add_habit(request):
    user_id = request.authenticated_userid
    if not user_id:
        return HTTPFound(location=request.route_url('login'))

    if request.method == 'POST':
        name = request.params.get('name', '').strip()
        description = request.params.get('description', '').strip()
        difficulty = request.params.get('difficulty')
        frequency_label = request.params.get('frequency')

        errors = []

        if not name or len(name) < 2:
            errors.append("El nombre del hábito es obligatorio y debe tener al menos 2 caracteres.")

        if difficulty not in ['Bajo', 'Medio', 'Alto']:
            errors.append("El grado de dificultad no es válido.")

        frequency_map = {
            'Diario': 1,
            'Semanal': 7,
            'Mensual': 30,
            'Otra': 0
        }

        frequency = frequency_map.get(frequency_label)
        if frequency is None:
            errors.append("La frecuencia debe ser una opción válida.")

        if errors:
            return {
                'errors': errors,
                'name': name,
                'description': description,
                'difficulty': difficulty,
                'frequency': frequency_label,
            }

        habit = Habit(
            name=name,
            description=description,
            difficulty=difficulty,
            frequency=frequency,
            user_id=user_id
        )
        DBSession.add(habit)
        DBSession.commit()

        return HTTPFound(location=request.route_url('home'))

    return {}

@view_config(route_name='complete_habit')
def complete_habit(request):
    user_id = request.authenticated_userid
    if not user_id:
        return HTTPFound(location=request.route_url('login'))

    habit_id = request.matchdict.get('id')

    # Verificar que el hábito pertenece al usuario actual
    habit = request.dbsession.query(Habit).filter_by(id=habit_id, user_id=user_id).first()

    if not habit:
        return HTTPFound(location=request.route_url('home'))

    today = datetime.utcnow().date()

    existing_progress = request.dbsession.query(HabitProgress).filter(
        HabitProgress.habit_id == habit.id,
        HabitProgress.date >= datetime.combine(today, datetime.min.time()),
        HabitProgress.date <= datetime.combine(today, datetime.max.time())
    ).first()

    if not existing_progress:
        progress = HabitProgress(
            habit_id=habit.id,
            date=datetime.utcnow()
        )
        request.dbsession.add(progress)
        request.dbsession.commit()

    # Redirigir con ?completed=1 para activar el Toast
    return HTTPFound(location=request.route_url('home', _query={'completed': '1'}))


@view_config(route_name='delete_habit')
def delete_habit_view(request):
    try:
        habit_id = int(request.matchdict['id'])
    except (KeyError, ValueError):
        request.session.flash('ID inválido.', 'error')
        return HTTPFound(location=request.route_url('home'))

    habit = DBSession.query(Habit).filter_by(id=habit_id).first()

    if habit:
        DBSession.delete(habit)
        DBSession.commit()
        request.session.flash(f'Hábito "{habit.name}" eliminado.', 'success')
    else:
        request.session.flash('Hábito no encontrado.', 'error')

    return HTTPFound(location=request.route_url('home'))

@view_config(route_name='edit_habit', renderer='templates/edit_habit.jinja2', request_method=['GET', 'POST'])
def edit_habit(request):
    habit_id = request.matchdict.get('id')
    habit = request.dbsession.query(Habit).filter_by(id=habit_id).first()

    if not habit:
        return HTTPFound(location=request.route_url('home'))

    errors = []

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        difficulty = request.POST.get('difficulty', '').strip()
        frequency = request.POST.get('frequency', '').strip()

        if len(name) < 2:
            errors.append('El nombre debe tener al menos 2 caracteres')
        if difficulty not in ['Bajo', 'Medio', 'Alto']:
            errors.append('Grado de dificultad inválido')
        if frequency not in ['Diario', 'Semanal', 'Mensual', 'Otra']:
            errors.append('Frecuencia inválida')

        if not errors:
            habit.name = name
            habit.description = description
            habit.difficulty = difficulty
            habit.frequency = frequency

            # Aquí usamos commit() en vez de flush()
            request.dbsession.commit()

            return HTTPFound(location=request.route_url('home'))

        return {
            'errors': errors,
            'name': name,
            'description': description,
            'difficulty': difficulty,
            'frequency': frequency,
            'habit': habit,
        }

    return {
        'name': habit.name,
        'description': habit.description,
        'difficulty': habit.difficulty,
        'frequency': habit.frequency,
        'habit': habit,
        'errors': [],
    }
    
@view_config(route_name='progress', renderer='templates/progress.jinja2')
def progress_view(request):
    user_id = request.authenticated_userid
    if not user_id:
        return HTTPFound(location=request.route_url('login'))

    habits = request.dbsession.query(Habit).filter_by(user_id=user_id).all()

    today = datetime.utcnow()
    seven_days_ago = today - timedelta(days=7)

    habit_progress = {}
    for habit in habits:
        count = request.dbsession.query(func.count(HabitProgress.id)).filter(
            HabitProgress.habit_id == habit.id,
            HabitProgress.date >= seven_days_ago
        ).scalar()

        habit_progress[habit.name] = count

    return {
        'habit_progress': habit_progress,
        'max_days': 7
    }