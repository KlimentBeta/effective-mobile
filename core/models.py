from django.db import models
from django.contrib.auth.hashers import make_password, check_password

class User(models.Model):
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    id = models.AutoField(primary_key=True)
    last_name = models.CharField("Фамилия", max_length=50)
    first_name = models.CharField("Имя", max_length=50)
    middle_name = models.CharField("Отчество", max_length=50, blank=True, null=True)
    email = models.EmailField("Email", unique=True)
    password_hash = models.CharField("Пароль (hash)", max_length=255)
    is_active = models.BooleanField("Активен", default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f"{self.last_name} {self.first_name} ({self.email})"

    def set_password(self, raw_password):
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password_hash)

    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_anonymous(self):
        return False
    
    def is_staff(self):
        return False
    
    def is_superuser(self):
        return False