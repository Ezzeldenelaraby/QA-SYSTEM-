from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User
from .forms import UserLoginForm, UserCreateForm, UserEditForm
from apps.core.utils import log_audit

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    form = UserLoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        log_audit(user, 'LOGIN', 'Accounts', user.id, user.username, notes='User successfully logged into QMS Hub')
        messages.success(request, f"Welcome back, {user.full_name}!")
        next_url = request.GET.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('dashboard:index')

    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    if request.user.is_authenticated:
        log_audit(request.user, 'LOGOUT', 'Accounts', request.user.id, request.user.username)
        logout(request)
        messages.info(request, "You have been logged out successfully.")
    return redirect('accounts:login')

@login_required
def user_list_view(request):
    if not (request.user.is_superuser or request.user.role in ['SUPER_ADMIN', 'QA_MANAGER', 'DEPARTMENT_HEAD']):
        messages.error(request, "Access restricted to Administrators and QA Management.")
        return redirect('dashboard:index')

    users = User.objects.select_related('department').all().order_by('username')
    return render(request, 'accounts/user_list.html', {'users': users})

@login_required
def user_create_view(request):
    if not (request.user.is_superuser or request.user.role in ['SUPER_ADMIN', 'QA_MANAGER']):
        messages.error(request, "Only Super Admin or QA Manager can register new system users.")
        return redirect('accounts:user_list')

    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            new_user = form.save()
            log_audit(request.user, 'CREATE', 'User', new_user.id, new_user.username, notes=f'Created user with role {new_user.role}')
            messages.success(request, f"User {new_user.username} successfully created.")
            return redirect('accounts:user_list')
    else:
        form = UserCreateForm()

    return render(request, 'accounts/user_form.html', {'form': form, 'title': 'Create New System User'})

@login_required
def user_edit_view(request, user_id):
    if not (request.user.is_superuser or request.user.role in ['SUPER_ADMIN', 'QA_MANAGER']):
        messages.error(request, "Only Super Admin or QA Manager can edit user privileges.")
        return redirect('accounts:user_list')

    target_user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        form = UserEditForm(request.POST, instance=target_user)
        if form.is_valid():
            form.save()
            log_audit(request.user, 'UPDATE', 'User', target_user.id, target_user.username, notes=f'Updated role to {target_user.role}')
            messages.success(request, f"User {target_user.username} updated successfully.")
            return redirect('accounts:user_list')
    else:
        form = UserEditForm(instance=target_user)

    return render(request, 'accounts/user_form.html', {'form': form, 'title': f'Edit User: {target_user.username}', 'target_user': target_user})

@login_required
def profile_view(request):
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', request.user.first_name)
        request.user.last_name = request.POST.get('last_name', request.user.last_name)
        request.user.email = request.POST.get('email', request.user.email)
        request.user.phone = request.POST.get('phone', request.user.phone)
        request.user.save()
        messages.success(request, "Your profile details have been updated.")
        return redirect('accounts:profile')

    return render(request, 'accounts/profile.html')
