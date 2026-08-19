import csv
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from django.urls import reverse_lazy

from django.core.paginator import Paginator
from .models import Project, Threat, UserProfile
from .forms import SignUpForm, ProjectForm, ThreatForm, UserUpdateForm, UserProfileForm


class CustomLoginView(LoginView):
    template_name = 'analysis/login.html'


def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created successfully. Welcome!")
            return redirect('dashboard')
    else:
        form = SignUpForm()
    return render(request, 'analysis/signup.html', {'form': form})


@login_required
def dashboard(request):
    projects = Project.objects.filter(owner=request.user)
    all_threats = Threat.objects.filter(project__owner=request.user)

    total_threats = all_threats.count()
    critical_count = sum(1 for t in all_threats if t.risk_level == 'Critical')
    high_count = sum(1 for t in all_threats if t.risk_level == 'High')
    open_count = all_threats.filter(status='open').count()

    overall_breakdown = {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0}
    for t in all_threats:
        overall_breakdown[t.risk_level] += 1

    top_threats = sorted(all_threats, key=lambda t: t.dread_score, reverse=True)[:5]

    context = {
        'projects': projects,
        'total_threats': total_threats,
        'critical_count': critical_count,
        'high_count': high_count,
        'open_count': open_count,
        'risk_counts': overall_breakdown,
        'top_threats': top_threats,
    }
    return render(request, 'analysis/dashboard.html', context)


@login_required
def profile_view(request):
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        # Create a profile if the user doesn't have one
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        profile_form = UserProfileForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        profile_form = UserProfileForm(instance=profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    return render(request, 'analysis/profile.html', context)


@login_required
def project_list(request):
    projects = Project.objects.filter(owner=request.user)
    return render(request, 'analysis/project_list.html', {'projects': projects, 'object_list': projects})


@login_required
def project_create(request):
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            messages.success(request, f'Project "{project.name}" created.')
            return redirect('project_detail', pk=project.pk)
    else:
        form = ProjectForm()
    return render(request, 'analysis/project_form.html', {'form': form, 'title': 'New Project'})


@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    all_threats = list(project.threats.all())

    status_filter = request.GET.get('status')
    risk_filter = request.GET.get('risk')
    search = request.GET.get('search') or request.GET.get('q')

    filtered_threats = all_threats
    if status_filter:
        filtered_threats = [t for t in filtered_threats if t.status == status_filter]
    if search:
        search_lower = search.lower()
        filtered_threats = [t for t in filtered_threats if search_lower in t.title.lower() or search_lower in t.description.lower()]
    if risk_filter:
        filtered_threats = [t for t in filtered_threats if t.risk_level == risk_filter]

    # Sorting
    sort = request.GET.get('sort')
    direction = request.GET.get('dir', 'asc')
    if sort == 'title':
        filtered_threats.sort(key=lambda t: t.title.lower(), reverse=(direction == 'desc'))
    elif sort == 'score':
        filtered_threats.sort(key=lambda t: t.dread_score, reverse=(direction == 'desc'))
    elif sort == 'status':
        filtered_threats.sort(key=lambda t: t.status, reverse=(direction == 'desc'))

    risk_counts = {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0}
    for t in all_threats:
        risk_counts[t.risk_level] += 1

    paginator = Paginator(filtered_threats, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'project': project,
        'threats': filtered_threats,
        'page_obj': page_obj,
        'status_filter': status_filter or '',
        'risk_filter': risk_filter or '',
        'search': search or '',
        'risk_counts': risk_counts,
    }
    return render(request, 'analysis/project_detail.html', context)


@login_required
def project_edit(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project updated.')
            return redirect('project_detail', pk=project.pk)
    else:
        form = ProjectForm(instance=project)
    return render(request, 'analysis/project_form.html', {'form': form, 'title': 'Edit Project'})


@login_required
def project_delete(request, pk):
    project = get_object_or_404(Project, pk=pk, owner=request.user)
    if request.method == 'POST':
        name = project.name
        project.delete()
        messages.success(request, f'Project "{name}" deleted.')
        return redirect('project_list')
    return render(request, 'analysis/confirm_delete.html', {'object': project, 'type': 'project', 'item_name': project.name})


@login_required
def threat_create(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk, owner=request.user)
    if request.method == 'POST':
        form = ThreatForm(request.POST)
        if form.is_valid():
            threat = form.save(commit=False)
            threat.project = project
            threat.created_by = request.user
            threat.save()
            messages.success(request, f'Threat "{threat.title}" added — risk score {threat.dread_score} ({threat.risk_level}).')
            return redirect('project_detail', pk=project.pk)
    else:
        form = ThreatForm()
    return render(request, 'analysis/threat_form.html', {'form': form, 'project': project, 'title': 'New Threat'})


@login_required
def threat_detail(request, pk):
    threat = get_object_or_404(Threat, pk=pk, project__owner=request.user)
    return render(request, 'analysis/threat_detail.html', {'threat': threat})


@login_required
def threat_edit(request, pk):
    threat = get_object_or_404(Threat, pk=pk, project__owner=request.user)
    if request.method == 'POST':
        form = ThreatForm(request.POST, instance=threat)
        if form.is_valid():
            form.save()
            messages.success(request, 'Threat updated.')
            return redirect('threat_detail', pk=threat.pk)
    else:
        form = ThreatForm(instance=threat)
    return render(request, 'analysis/threat_form.html', {'form': form, 'project': threat.project, 'title': 'Edit Threat'})


@login_required
def threat_delete(request, pk):
    threat = get_object_or_404(Threat, pk=pk, project__owner=request.user)
    project_pk = threat.project.pk
    if request.method == 'POST':
        title = threat.title
        threat.delete()
        messages.success(request, f'Threat "{title}" deleted.')
        return redirect('project_detail', pk=project_pk)
    return render(request, 'analysis/confirm_delete.html', {'object': threat, 'type': 'threat', 'item_name': threat.title})


@login_required
def export_csv(request, project_pk):
    project = get_object_or_404(Project, pk=project_pk, owner=request.user)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{project.name}_dread_report.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Title', 'STRIDE Category', 'Damage', 'Reproducibility', 'Exploitability',
        'Affected Users', 'Discoverability', 'DREAD Score', 'Risk Level', 'Status', 'Mitigation'
    ])
    for t in project.threats.all():
        writer.writerow([
            t.title, t.get_stride_category_display(), t.damage, t.reproducibility,
            t.exploitability, t.affected_users, t.discoverability, t.dread_score,
            t.risk_level, t.get_status_display(), t.mitigation
        ])
    return response
