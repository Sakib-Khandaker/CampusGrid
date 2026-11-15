from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from accounts.decorators import admin_required, teacher_required
from accounts.models import User, Student

from .forms import SessionForm, SemesterForm, NewsAndEventsForm, NoticeForm
from .models import NewsAndEvents, ActivityLog, Session, Semester, Notice


# ########################################################
# NEWS & EVENTS
# ########################################################
@login_required
def home_view(request):
    items = NewsAndEvents.objects.all().order_by("-updated_date")
    return render(request, "core/index.html", {
        "title": "News & Events",
        "items": items,
    })

# =====================================================
# NOTICES (PUBLIC VIEW)
# =====================================================
@login_required
def notices_view(request):
    notices = Notice.objects.all().order_by("-updated_at")
    return render(request, "core/notices.html", {
        "title": "Notices",
        "notices": notices,
    })


# =====================================================
# ADD NOTICE (ADMIN ONLY)
# =====================================================
@login_required
@admin_required
def add_notice(request):
    form = NoticeForm(request.POST or None, request.FILES or None)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Notice created successfully.")
            return redirect("notices")

    return render(request, "core/add_notice.html", {
        "form": form
    })


# =====================================================
# EDIT NOTICE
# =====================================================
@login_required
@admin_required
def edit_notice(request, pk):
    notice = get_object_or_404(Notice, pk=pk)

    form = NoticeForm(
        request.POST or None,
        request.FILES or None,
        instance=notice
    )

    if request.method == "POST":
        if form.is_valid():
            form.save()
            messages.success(request, "Notice updated successfully.")
            return redirect("notices")

    return render(request, "core/add_notice.html", {
        "form": form,
        "notice": notice
    })


# =====================================================
# DELETE NOTICE
# =====================================================
@login_required
@admin_required
def delete_notice(request, pk):
    notice = get_object_or_404(Notice, pk=pk)

    if request.method == "POST":
        notice.delete()
        messages.success(request, "Notice deleted successfully.")
        return redirect("notices")

    return render(request, "core/confirm_delete.html", {
        "object": notice,
        "type": "Notice"
    })
# ########################################################
# CURRICULUM
# ########################################################
@login_required
def curriculum_view(request):
    return render(request, "core/curriculum.html", {
        "title": "Curriculum"
    })


# ########################################################
# DASHBOARD
# ########################################################
@login_required
@admin_required
def dashboard_view(request):
    logs = ActivityLog.objects.all().order_by("-created_at")[:10]
    gender_count = Student.get_gender_count()

    return render(request, "core/dashboard.html", {
        "student_count": User.objects.get_student_count(),
        "teacher_count": User.objects.get_teacher_count(),
        "superuser_count": User.objects.get_superuser_count(),
        "males_count": gender_count["M"],
        "females_count": gender_count["F"],
        "logs": logs,
    })


# ########################################################
# NEWS CRUD
# ########################################################
@login_required
def post_add(request):
    if request.method == "POST":
        form = NewsAndEventsForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Post uploaded successfully.")
            return redirect("home")
    else:
        form = NewsAndEventsForm()

    return render(request, "core/post_add.html", {"form": form})


@login_required
@teacher_required
def edit_post(request, pk):
    post = get_object_or_404(NewsAndEvents, pk=pk)

    if request.method == "POST":
        form = NewsAndEventsForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, "Post updated successfully.")
            return redirect("home")
    else:
        form = NewsAndEventsForm(instance=post)

    return render(request, "core/post_add.html", {"form": form})


@login_required
@teacher_required
def delete_post(request, pk):
    post = get_object_or_404(NewsAndEvents, pk=pk)
    post.delete()
    messages.success(request, "Post deleted successfully.")
    return redirect("home")


# ########################################################
# SESSION
# ########################################################
@login_required
@teacher_required
def session_list_view(request):
    sessions = Session.objects.all().order_by("-is_current_session", "-session")
    return render(request, "core/session_list.html", {"sessions": sessions})


@login_required
@teacher_required
def session_add_view(request):
    form = SessionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if form.cleaned_data.get("is_current_session"):
            unset_current_session()
        form.save()
        return redirect("session_list")

    return render(request, "core/session_update.html", {"form": form})


@login_required
@teacher_required
def session_update_view(request, pk):
    session = get_object_or_404(Session, pk=pk)
    form = SessionForm(request.POST or None, instance=session)

    if request.method == "POST" and form.is_valid():
        if form.cleaned_data.get("is_current_session"):
            unset_current_session()
        form.save()
        return redirect("session_list")

    return render(request, "core/session_update.html", {"form": form})


@login_required
@teacher_required
def session_delete_view(request, pk):
    session = get_object_or_404(Session, pk=pk)

    if session.is_current_session:
        messages.error(request, "Cannot delete current session.")
    else:
        session.delete()
        messages.success(request, "Session deleted.")

    return redirect("session_list")


def unset_current_session():
    Session.objects.filter(is_current_session=True).update(is_current_session=False)


# ########################################################
# SEMESTER
# ########################################################
@login_required
@teacher_required
def semester_list_view(request):
    semesters = Semester.objects.all().order_by("-is_current_semester", "-semester")
    return render(request, "core/semester_list.html", {"semesters": semesters})


@login_required
@teacher_required
def semester_add_view(request):
    form = SemesterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        if form.cleaned_data.get("is_current_semester"):
            unset_current_semester()
            unset_current_session()
        form.save()
        return redirect("semester_list")

    return render(request, "core/semester_update.html", {"form": form})


@login_required
@teacher_required
def semester_update_view(request, pk):
    semester = get_object_or_404(Semester, pk=pk)
    form = SemesterForm(request.POST or None, instance=semester)

    if request.method == "POST" and form.is_valid():
        if form.cleaned_data.get("is_current_semester"):
            unset_current_semester()
            unset_current_session()
        form.save()
        return redirect("semester_list")

    return render(request, "core/semester_update.html", {"form": form})


@login_required
@teacher_required
def semester_delete_view(request, pk):
    semester = get_object_or_404(Semester, pk=pk)

    if semester.is_current_semester:
        messages.error(request, "Cannot delete current semester.")
    else:
        semester.delete()
        messages.success(request, "Semester deleted.")

    return redirect("semester_list")


def unset_current_semester():
    Semester.objects.filter(is_current_semester=True).update(is_current_semester=False)