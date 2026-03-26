from django.shortcuts import render, redirect
from core.models import User

def index(request):
    user_id = request.session.get('user_id')
    current_user = User.objects.filter(id=user_id, is_active=True).first() if user_id else None
    
    return render(request, 'index.html', {'current_user': current_user})

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password')
        
        user = User.objects.filter(email=email).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                return render(request, 'login.html', {'error': 'Аккаунт деактивирован'})
            
            request.session['user_id'] = user.id
            return redirect('index')
        
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