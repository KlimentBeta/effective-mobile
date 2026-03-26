from django.http import HttpResponseForbidden, JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from core.models import Post, Role, User, UserRole
from core.jwt_utils import create_access_token
from django.urls import reverse

def index(request):
    user_id = request.session.get('user_id')
    current_user = None
    user_role_name = None
    
    if user_id:
        current_user = User.objects.filter(id=user_id, is_active=True).first()
        if current_user:
            user_role = UserRole.objects.filter(user=current_user).select_related('role').first()
            user_role_name = user_role.role.name if user_role else None
    
    posts = Post.objects.all()
    
    return render(request, 'index.html', {
        'current_user': current_user,
        'user_role': user_role_name,
        'posts': posts
    })

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password')
        
        user = User.objects.filter(email=email).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                return render(request, 'login.html', {'error': 'Аккаунт деактивирован'})
            
            token = create_access_token(user.id, user.email)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'token': token, 'user_id': user.id})
            
            request.session['user_id'] = user.id
            request.session['jwt_token'] = token
            response = redirect('index')
            response.set_cookie('jwt_token', token, httponly=True, max_age=3600)
            return response
        
        return render(request, 'login.html', {'error': 'Неверный email или пароль'})
    
    return render(request, 'login.html')

def register_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        middle_name = request.POST.get('middle_name', '').strip()
        
        if not email or not password:
            return render(request, 'register.html', {'error': 'Email и пароль обязательны'})
        
        if password != password_confirm:
            return render(request, 'register.html', {'error': 'Пароли не совпадают'})
        
        if User.objects.filter(email=email).exists():
            return render(request, 'register.html', {'error': 'Пользователь с таким email уже существует'})
        
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name if middle_name else None
        )
        
        user.set_password(password)
        user.save()
        
        default_role = Role.objects.filter(name='user').first()
        if default_role:
            UserRole.objects.create(user=user, role=default_role)
        
        return redirect('login')
    
    return render(request, 'register.html')
def profile_view(request):
    user_id = request.session.get('user_id')
    current_user = User.objects.filter(id=user_id, is_active=True).first() if user_id else None
    
    if not current_user:
        return redirect('login')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        middle_name = request.POST.get('middle_name', '').strip()
        new_password = request.POST.get('new_password')
        new_password_confirm = request.POST.get('new_password_confirm')
        
        if email != current_user.email and User.objects.filter(email=email).exists():
            return render(request, 'profile.html', {
                'current_user': current_user,
                'error': 'Пользователь с таким email уже существует'
            })
        
        if new_password:
            if new_password != new_password_confirm:
                return render(request, 'profile.html', {
                    'current_user': current_user,
                    'error': 'Пароли не совпадают'
                })
            if len(new_password) < 6:
                return render(request, 'profile.html', {
                    'current_user': current_user,
                    'error': 'Пароль должен быть не менее 6 символов'
                })
            current_user.set_password(new_password)
        
        current_user.email = email
        current_user.first_name = first_name
        current_user.last_name = last_name
        current_user.middle_name = middle_name if middle_name else None
        current_user.save()
        
        return render(request, 'profile.html', {
            'current_user': current_user,
            'success': 'Профиль успешно обновлён!'
        })
    
    return render(request, 'profile.html', {'current_user': current_user})

def delete_account_view(request):
    if request.method != 'POST':
        return redirect('profile')
    
    user_id = request.session.get('user_id')
    current_user = User.objects.filter(id=user_id, is_active=True).first()
    
    if not current_user:
        return redirect('login')
    
    password = request.POST.get('confirm_password')
    if not current_user.check_password(password):
        return render(request, 'profile.html', {
            'current_user': current_user,
            'error': 'Неверный пароль. Удаление отменено.'
        })
    
    current_user.is_active = False
    current_user.save()
    
    request.session.flush()
    
    return redirect('index')

def logout_view(request):
    request.session.flush() 
    return redirect('index')

def admin_panel(request):
    user_id = request.session.get('user_id')
    current_user = User.objects.filter(id=user_id, is_active=True).first() if user_id else None
    
    if not current_user:
        return redirect('login')
    
    is_admin = UserRole.objects.filter(user=current_user, role__name='admin').exists()
    if not is_admin:
        return HttpResponseForbidden("Доступ запрещен")
    
    if request.method == 'POST' and request.POST.get('action') == 'change_role':
        target_user_id = request.POST.get('user_id')
        new_role_id = request.POST.get('role')
        
        if target_user_id and new_role_id:
            try:
                target_user = User.objects.get(id=target_user_id)
                new_role = Role.objects.get(id=new_role_id)
                
                UserRole.objects.filter(user=target_user).delete()
                UserRole.objects.create(user=target_user, role=new_role)
                
                return render(request, 'admin_panel.html', {
                    'current_user': current_user,
                    'success': f'Роль пользователя {target_user.email} изменена на {new_role.name}',
                    'roles': Role.objects.all(),
                    'users': User.objects.all()
                })
            except (User.DoesNotExist, Role.DoesNotExist):
                return render(request, 'admin_panel.html', {
                    'current_user': current_user,
                    'error': 'Ошибка при смене роли',
                    'roles': Role.objects.all(),
                    'users': User.objects.all()
                })
    
    if request.method == 'POST' and not request.POST.get('action'):
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        role_id = request.POST.get('role')
        
        if User.objects.filter(email=email).exists():
            return render(request, 'admin_panel.html', {
                'current_user': current_user,
                'error': 'Пользователь с таким email уже существует',
                'roles': Role.objects.all(),
                'users': User.objects.all()
            })
        
        new_user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            middle_name=request.POST.get('middle_name', '').strip()
        )
        new_user.set_password(password)
        new_user.save()
        
        if role_id:
            role = Role.objects.get(id=role_id)
            UserRole.objects.create(user=new_user, role=role)
        
        return render(request, 'admin_panel.html', {
            'current_user': current_user,
            'success': 'Пользователь создан',
            'roles': Role.objects.all(),
            'users': User.objects.all()
        })
    
    return render(request, 'admin_panel.html', {
        'current_user': current_user,
        'roles': Role.objects.all(),
        'users': User.objects.all()
    })

def edit_post(request, post_id):
    if request.method != 'POST':
        return redirect('index')
    
    user_id = request.session.get('user_id')
    current_user = User.objects.filter(id=user_id, is_active=True).first() if user_id else None
    
    if not current_user:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Unauthorized'}, status=401)
        return redirect('login')
    
    user_role = UserRole.objects.filter(user=current_user).select_related('role').first()
    role_name = user_role.role.name if user_role else None
    
    if role_name not in ['admin', 'manager']:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Forbidden'}, status=403)
        return render(request, 'errors/403.html', status=403)
    
    try:
        post = Post.objects.get(id=post_id)
        post.title = request.POST.get('title', '').strip()
        post.description = request.POST.get('description', '').strip()
        post.save()
    except Post.DoesNotExist:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Not found'}, status=404)
        return render(request, 'errors/404.html', status=404)
    
    return HttpResponseRedirect(reverse('index'))
