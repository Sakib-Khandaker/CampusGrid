from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.decorators import method_decorator
from django.views.generic import CreateView
from django_filters.views import FilterView

from accounts.decorators import teacher_required, student_required
from accounts.models import Student
from core.models import Semester
from course.filters import CourseAllocationFilter, AdmissionSessionFilter
from course.forms import (
    CourseAddForm,
    CourseAllocationForm,
    EditCourseAllocationForm,
    AdmissionSessionForm,
    UploadFormFile,
    UploadFormVideo,
)
from course.models import (
    Course,
    CourseAllocation,
    AdmissionSession,
    Upload,
    UploadVideo,
)
from result.models import TakenCourse

# ============================
# ADMIN ONLY DECORATOR
# ============================
def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


# ============================
# PROGRAM LIST (ALL USERS)
# ============================
@method_decorator(login_required, name="dispatch")
class AdmissionSessionFilterView(FilterView):
    filterset_class = AdmissionSessionFilter
    template_name = "course/admission_session_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "AdmissionSessions"
        return context


# ============================
# PROGRAM DETAIL (ALL USERS)
# ============================
@login_required
def admission_session_detail(request, pk):
    admission_session = get_object_or_404(AdmissionSession, pk=pk)
    courses = Course.objects.filter(admission_session_id=pk).annotate(
    type_order=Case(
        When(course_type='theory', then=0),
        When(course_type='lab', then=1),
        When(course_type='internship', then=2),
        When(course_type='viva', then=3),
        output_field=IntegerField(),
    )
).order_by("year", "semester", "type_order")
    credits = courses.aggregate(total_credits=Sum("credit"))

    paginator = Paginator(courses, 10)
    page = request.GET.get("page")
    courses = paginator.get_page(page)

    return render(
        request,
        "course/admission_session_single.html",
        {
            "title": admission_session.title,
            "admission_session": admission_session,
            "courses": courses,
            "credits": credits,
        },
    )


# ============================
# PROGRAM ADD (ADMIN ONLY)
# ============================
@login_required
@admin_required
def admission_session_add(request):
    if request.method == "POST":
        form = AdmissionSessionForm(request.POST)
        if form.is_valid():
            admission_session = form.save()
            messages.success(request, f"{admission_session.title} admission session has been created.")
            return redirect("admission_sessions")
        messages.error(request, "Correct the error(s) below.")
    else:
        form = AdmissionSessionForm()

    return render(
        request,
        "course/admission_session_add.html",
        {"title": "Add AdmissionSession", "form": form},
    )


# ============================
# PROGRAM EDIT (ADMIN ONLY)
# ============================
@login_required
@admin_required
def admission_session_edit(request, pk):
    admission_session = get_object_or_404(AdmissionSession, pk=pk)

    if request.method == "POST":
        form = AdmissionSessionForm(request.POST, instance=admission_session)
        if form.is_valid():
            admission_session = form.save()
            messages.success(request, f"{admission_session.title} admission session has been updated.")
            return redirect("admission_sessions")
        messages.error(request, "Correct the error(s) below.")
    else:
        form = AdmissionSessionForm(instance=admission_session)

    return render(
        request,
        "course/admission_session_add.html",
        {"title": "Edit AdmissionSession", "form": form},
    )


# ============================
# PROGRAM DELETE (ADMIN ONLY)
# ============================
@login_required
@admin_required
def admission_session_delete(request, pk):
    admission_session = get_object_or_404(AdmissionSession, pk=pk)
    title = admission_session.title
    admission_session.delete()
    messages.success(request, f"AdmissionSession {title} has been deleted.")
    return redirect("admission_sessions")

# ########################################################
# Course Views
# ########################################################


@login_required
def course_single(request, slug):
    course = get_object_or_404(Course, slug=slug)

    # ============================
    # ACCESS CONTROL (IMPORTANT FIX)
    # ============================
    if request.user.is_teacher:
        is_allowed = CourseAllocation.objects.filter(
            teacher=request.user,
            courses=course
        ).exists()

        if not is_allowed:
            messages.error(request, "You are not allowed to access this course.")
            return redirect("admission_sessions")  # or "course_list"

    # Students can access only if registered (optional rule)
    if request.user.is_student:
        student = get_object_or_404(Student, student__pk=request.user.id)
        is_registered = TakenCourse.objects.filter(
            student=student,
            course=course
        ).exists()

        if not is_registered:
            messages.error(request, "You are not registered in this course.")
            return redirect("course_registration")

    # ============================
    # ORIGINAL LOGIC
    # ============================
    files = Upload.objects.filter(course__slug=slug)
    videos = UploadVideo.objects.filter(course__slug=slug)

    teachers = CourseAllocation.objects.filter(courses__pk=course.id)

    return render(
        request,
        "course/course_single.html",
        {
            "title": course.title,
            "course": course,
            "files": files,
            "videos": videos,
            "teachers": teachers,
            "media_url": settings.MEDIA_URL,
        },
    )

@login_required
@teacher_required
def course_add(request, pk):
    admission_session = get_object_or_404(AdmissionSession, pk=pk)
    if request.method == "POST":
        form = CourseAddForm(request.POST)
        if form.is_valid():
            course = form.save()
            messages.success(
                request, f"{course.title} ({course.code}) has been created."
            )
            return redirect("admission_session_detail", pk=admission_session.pk)
        messages.error(request, "Correct the error(s) below.")
    else:
        form = CourseAddForm(initial={"admission_session": admission_session})
    return render(
        request,
        "course/course_add.html",
        {"title": "Add Course", "form": form, "admission_session": admission_session},
    )


@login_required
@teacher_required
def course_edit(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if request.method == "POST":
        form = CourseAddForm(request.POST, instance=course)
        if form.is_valid():
            course = form.save()
            messages.success(
                request, f"{course.title} ({course.code}) has been updated."
            )
            return redirect("admission_session_detail", pk=course.admission_session.pk)
        messages.error(request, "Correct the error(s) below.")
    else:
        form = CourseAddForm(instance=course)
    return render(
        request, "course/course_add.html", {"title": "Edit Course", "form": form}
    )


@login_required
@teacher_required
def course_delete(request, slug):
    course = get_object_or_404(Course, slug=slug)
    title = course.title
    admission_session_id = course.AdmissionSession.id
    course.delete()
    messages.success(request, f"Course {title} has been deleted.")
    return redirect("admission_session_detail", pk=admission_session_id)


# ########################################################
# Course Allocation Views
# ########################################################


@method_decorator([login_required, teacher_required], name="dispatch")
class CourseAllocationFormView(CreateView):
    form_class = CourseAllocationForm
    template_name = "course/course_allocation_form.html"

    def form_valid(self, form):
        teacher = form.cleaned_data["teacher"]
        selected_courses = form.cleaned_data["courses"]
        allocation, created = CourseAllocation.objects.get_or_create(teacher=teacher)
        allocation.courses.set(selected_courses)
        messages.success(
            self.request, f"Courses allocated to {teacher.get_full_name} successfully."
        )
        return redirect("course_allocation_view")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Assign Course"
        return context


@method_decorator([login_required, teacher_required], name="dispatch")
class CourseAllocationFilterView(FilterView):
    filterset_class = CourseAllocationFilter
    template_name = "course/course_allocation_view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Course Allocations"
        return context


@login_required
@teacher_required
def edit_allocated_course(request, pk):
    allocation = get_object_or_404(CourseAllocation, pk=pk)
    if request.method == "POST":
        form = EditCourseAllocationForm(request.POST, instance=allocation)
        if form.is_valid():
            form.save()
            messages.success(request, "Course allocation has been updated.")
            return redirect("course_allocation_view")
        messages.error(request, "Correct the error(s) below.")
    else:
        form = EditCourseAllocationForm(instance=allocation)
    return render(
        request,
        "course/course_allocation_form.html",
        {"title": "Edit Course Allocation", "form": form},
    )


@login_required
@teacher_required
def deallocate_course(request, pk):
    allocation = get_object_or_404(CourseAllocation, pk=pk)
    allocation.delete()
    messages.success(request, "Successfully deallocated courses.")
    return redirect("course_allocation_view")


# ########################################################
# File Upload Views
# ########################################################


@login_required
@teacher_required
def handle_file_upload(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if request.method == "POST":
        form = UploadFormFile(request.POST, request.FILES)
        if form.is_valid():
            upload = form.save(commit=False)
            upload.course = course
            upload.save()
            messages.success(request, f"{upload.title} has been uploaded.")
            return redirect("course_detail", slug=slug)
        messages.error(request, "Correct the error(s) below.")
    else:
        form = UploadFormFile()
    return render(
        request,
        "upload/upload_file_form.html",
        {"title": "File Upload", "form": form, "course": course},
    )


@login_required
@teacher_required
def handle_file_edit(request, slug, file_id):
    course = get_object_or_404(Course, slug=slug)
    upload = get_object_or_404(Upload, pk=file_id)
    if request.method == "POST":
        form = UploadFormFile(request.POST, request.FILES, instance=upload)
        if form.is_valid():
            upload = form.save()
            messages.success(request, f"{upload.title} has been updated.")
            return redirect("course_detail", slug=slug)
        messages.error(request, "Correct the error(s) below.")
    else:
        form = UploadFormFile(instance=upload)
    return render(
        request,
        "upload/upload_file_form.html",
        {"title": "Edit File", "form": form, "course": course},
    )


@login_required
@teacher_required
def handle_file_delete(request, slug, file_id):
    upload = get_object_or_404(Upload, pk=file_id)
    title = upload.title
    upload.delete()
    messages.success(request, f"{title} has been deleted.")
    return redirect("course_detail", slug=slug)


# ########################################################
# Video Upload Views
# ########################################################


@login_required
@teacher_required
def handle_video_upload(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if request.method == "POST":
        form = UploadFormVideo(request.POST, request.FILES)
        if form.is_valid():
            video = form.save(commit=False)
            video.course = course
            video.save()
            messages.success(request, f"{video.title} has been uploaded.")
            return redirect("course_detail", slug=slug)
        messages.error(request, "Correct the error(s) below.")
    else:
        form = UploadFormVideo()
    return render(
        request,
        "upload/upload_video_form.html",
        {"title": "Video Upload", "form": form, "course": course},
    )


@login_required
def handle_video_single(request, slug, video_slug):
    course = get_object_or_404(Course, slug=slug)
    video = get_object_or_404(UploadVideo, slug=video_slug)
    return render(
        request,
        "upload/video_single.html",
        {"video": video, "course": course},
    )


@login_required
@teacher_required
def handle_video_edit(request, slug, video_slug):
    course = get_object_or_404(Course, slug=slug)
    video = get_object_or_404(UploadVideo, slug=video_slug)
    if request.method == "POST":
        form = UploadFormVideo(request.POST, request.FILES, instance=video)
        if form.is_valid():
            video = form.save()
            messages.success(request, f"{video.title} has been updated.")
            return redirect("course_detail", slug=slug)
        messages.error(request, "Correct the error(s) below.")
    else:
        form = UploadFormVideo(instance=video)
    return render(
        request,
        "upload/upload_video_form.html",
        {"title": "Edit Video", "form": form, "course": course},
    )


@login_required
@teacher_required
def handle_video_delete(request, slug, video_slug):
    video = get_object_or_404(UploadVideo, slug=video_slug)
    title = video.title
    video.delete()
    messages.success(request, f"{title} has been deleted.")
    return redirect("course_detail", slug=slug)


# ########################################################
# Course Registration Views
# ########################################################


@login_required
@student_required
def course_registration(request):
    if request.method == "POST":
        student = Student.objects.get(student__pk=request.user.id)
        ids = ()
        data = request.POST.copy()
        data.pop("csrfmiddlewaretoken", None)  # remove csrf_token
        for key in data.keys():
            ids = ids + (str(key),)
        for s in range(0, len(ids)):
            course = Course.objects.get(pk=ids[s])
            obj = TakenCourse.objects.create(student=student, course=course)
            obj.save()
        messages.success(request, "Courses registered successfully!")
        return redirect("course_registration")
    else:
        current_semester = Semester.objects.filter(is_current_semester=True).first()
        if not current_semester:
            messages.error(request, "No active semester found.")
            return render(request, "course/course_registration.html")

        # student = Student.objects.get(student__pk=request.user.id)
        student = get_object_or_404(Student, student__id=request.user.id)
        taken_courses = TakenCourse.objects.filter(student__student__id=request.user.id)
        t = ()
        for i in taken_courses:
            t += (i.course.pk,)

        courses = (
            Course.objects.filter(
                admission_session__pk=student.admission_session.id,
                level=student.level,
                semester=current_semester,
            )
            .exclude(id__in=t)
            .order_by("year")
        )
        all_courses = Course.objects.filter(
            level=student.level, admission_session__pk=student.admission_session.id
        )

        no_course_is_registered = False  # Check if no course is registered
        all_courses_are_registered = False

        registered_courses = Course.objects.filter(level=student.level).filter(id__in=t)
        if (
            registered_courses.count() == 0
        ):  # Check if number of registered courses is 0
            no_course_is_registered = True

        if registered_courses.count() == all_courses.count():
            all_courses_are_registered = True

        total_first_semester_credit = 0
        total_sec_semester_credit = 0
        total_registered_credit = 0
        for i in courses:
            if i.semester == "First":
                total_first_semester_credit += float(i.credit)
            if i.semester == "Second":
                total_sec_semester_credit += float(i.credit)
        for i in registered_courses:
            total_registered_credit += float(i.credit)
        context = {
            "is_calender_on": True,
            "all_courses_are_registered": all_courses_are_registered,
            "no_course_is_registered": no_course_is_registered,
            "current_semester": current_semester,
            "courses": courses,
            "total_first_semester_credit": total_first_semester_credit,
            "total_sec_semester_credit": total_sec_semester_credit,
            "registered_courses": registered_courses,
            "total_registered_credit": total_registered_credit,
            "student": student,
        }
        return render(request, "course/course_registration.html", context)


@login_required
@student_required
def course_drop(request):
    if request.method == "POST":
        student = get_object_or_404(Student, student__pk=request.user.id)
        course_ids = request.POST.getlist("course_ids")
        print("course_ids", course_ids)
        for course_id in course_ids:
            course = get_object_or_404(Course, pk=course_id)
            TakenCourse.objects.filter(student=student, course=course).delete()
        messages.success(request, "Courses dropped successfully!")
        return redirect("course_registration")


# ########################################################
# User Course List View
# ########################################################
from django.db.models import Case, When, IntegerField

@login_required
def user_course_list(request):
    if request.user.is_teacher:
        courses = Course.objects.filter(
            allocated_course__teacher__pk=request.user.id
        ).annotate(
            type_order=Case(
                When(course_type='theory', then=0),
                When(course_type='lab', then=1),
                When(course_type='internship', then=2),
                When(course_type='viva', then=3),
                output_field=IntegerField(),
            )
        ).order_by("year", "semester", "type_order")

        return render(request, "course/user_course_list.html", {"courses": courses})

    if request.user.is_student:
        student = get_object_or_404(Student, student__pk=request.user.id)

        taken_courses = TakenCourse.objects.filter(student=student).select_related("course")

        return render(
            request,
            "course/user_course_list.html",
            {
                "student": student,
                "taken_courses": taken_courses,
            },
        )

    return render(request, "course/user_course_list.html")