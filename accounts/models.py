from django.db import models
from django.urls import reverse
from django.contrib.auth.models import AbstractUser, UserManager
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from PIL import Image

from course.models import AdmissionSession
from .validators import ASCIIUsernameValidator


# =========================
# LEVEL CHOICES
# =========================
BACHELOR_DEGREE = _("Bachelor")
MASTER_DEGREE = _("Master")

LEVEL = (
    (BACHELOR_DEGREE, _("Bachelor Degree")),
    (MASTER_DEGREE, _("Master Degree")),
)

# =========================
# RELATIONSHIP CHOICES
# =========================
FATHER = _("Father")
MOTHER = _("Mother")
BROTHER = _("Brother")
SISTER = _("Sister")
GRAND_MOTHER = _("Grand mother")
GRAND_FATHER = _("Grand father")
OTHER = _("Other")

RELATION_SHIP = (
    (FATHER, _("Father")),
    (MOTHER, _("Mother")),
    (BROTHER, _("Brother")),
    (SISTER, _("Sister")),
    (GRAND_MOTHER, _("Grand mother")),
    (GRAND_FATHER, _("Grand father")),
    (OTHER, _("Other")),
)

GENDERS = ((_("M"), _("Male")), (_("F"), _("Female")))


# =========================
# USER MANAGER
# =========================
class CustomUserManager(UserManager):
    def search(self, query=None):
        queryset = self.get_queryset()
        if query:
            queryset = queryset.filter(
                Q(username__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(email__icontains=query)
            ).distinct()
        return queryset

    def get_student_count(self):
        return self.model.objects.filter(is_student=True).count()

    def get_teacher_count(self):
        return self.model.objects.filter(is_teacher=True).count()

    def get_superuser_count(self):
        return self.model.objects.filter(is_superuser=True).count()


# =========================
# USER MODEL
# =========================
class User(AbstractUser):
    is_student = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)
    is_parent = models.BooleanField(default=False)
    is_dep_head = models.BooleanField(default=False)

    gender = models.CharField(max_length=1, choices=GENDERS, blank=True, null=True)
    phone = models.CharField(max_length=60, blank=True, null=True)
    address = models.CharField(max_length=60, blank=True, null=True)

    picture = models.ImageField(
        upload_to="profile_pictures/%y/%m/%d/",
        default="default.png",
        null=True
    )

    email = models.EmailField(blank=True, null=True)

    # =========================
    # ✅ DESIGNATION (NEW FIELD)
    # =========================
    DESIGNATION_CHOICES = (
        ('lecturer', _('Lecturer')),
        ('assistant_professor', _('Assistant Professor')),
        ('associate_professor', _('Associate Professor')),
        ('professor', _('Professor')),
    )

    designation = models.CharField(
        max_length=30,
        choices=DESIGNATION_CHOICES,
        default='Lecturer',
        blank=True,
        null=True
    )

    username_validator = ASCIIUsernameValidator()

    objects = CustomUserManager()

    class Meta:
        ordering = ("-date_joined",)

    @property
    def get_full_name(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.username

    def __str__(self):
        return f"{self.username} ({self.get_full_name})"

    @property
    def get_user_role(self):
        if self.is_superuser:
            return _("Admin")
        if self.is_student:
            return _("Student")
        if self.is_teacher:
            return _("Teacher")
        if self.is_parent:
            return _("Parent")
        return _("User")

    def get_picture(self):
        try:
            return self.picture.url
        except:
            return settings.MEDIA_URL + "default.png"

    def get_absolute_url(self):
        return reverse("profile_single", kwargs={"user_id": self.id})

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        try:
            img = Image.open(self.picture.path)
            if img.height > 300 or img.width > 300:
                img.thumbnail((300, 300))
                img.save(self.picture.path)
        except:
            pass

    def delete(self, *args, **kwargs):
        if self.picture and self.picture.url != settings.MEDIA_URL + "default.png":
            self.picture.delete()
        super().delete(*args, **kwargs)
# =========================
# STUDENT MANAGER
# =========================
class StudentManager(models.Manager):
    def search(self, query=None):
        qs = self.get_queryset()
        if query:
            qs = qs.filter(
                Q(level__icontains=query) |
                Q(admission_session__name__icontains=query)
            ).distinct()
        return qs

# =========================
# STUDENT MODEL
# =========================
class Student(models.Model):
    student = models.OneToOneField(User, on_delete=models.CASCADE)
    level = models.CharField(max_length=25, choices=LEVEL, null=True)
    admission_session = models.ForeignKey(AdmissionSession, on_delete=models.CASCADE, null=True)

    # ✅ NEW FIELDS
    id_dept = models.CharField(max_length=50, blank=True, null=True)
    registration_number = models.CharField(max_length=100, unique=True, blank=True, null=True)

    BLOOD_GROUP_CHOICES = (
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    )

    blood_group = models.CharField(
        max_length=5,
        choices=BLOOD_GROUP_CHOICES,
        blank=True,
        null=True
    )

    objects = StudentManager()

    class Meta:
        ordering = ("-student__date_joined",)

    def __str__(self):
        return self.student.get_full_name

    @classmethod
    def get_gender_count(cls):
        return {
            "M": Student.objects.filter(student__gender="M").count(),
            "F": Student.objects.filter(student__gender="F").count(),
        }

    def get_absolute_url(self):
        return reverse("profile_single", kwargs={"user_id": self.id})

    def delete(self, *args, **kwargs):
        self.student.delete()
        super().delete(*args, **kwargs)
# =========================
# PARENT MODEL
# =========================
class Parent(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student = models.OneToOneField(Student, null=True, on_delete=models.SET_NULL)

    first_name = models.CharField(max_length=120)
    last_name = models.CharField(max_length=120)

    phone = models.CharField(max_length=60, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    relation_ship = models.CharField(
        choices=RELATION_SHIP,
        max_length=20,
        blank=True
    )

    class Meta:
        ordering = ("-user__date_joined",)

    def __str__(self):
        return self.user.username


# =========================
# DEPARTMENT HEAD
# =========================
class DepartmentHead(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.ForeignKey(AdmissionSession, on_delete=models.CASCADE, null=True)

    class Meta:
        ordering = ("-user__date_joined",)

    def __str__(self):
        return str(self.user)