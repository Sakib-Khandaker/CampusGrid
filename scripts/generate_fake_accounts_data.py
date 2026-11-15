import os
import django
from typing import List, Tuple
from django.utils import timezone
from faker import Faker
from factory.django import DjangoModelFactory
from factory import SubFactory, LazyAttribute, Iterator
from django_extensions.management.commands import runscript

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from accounts.models import User, Student, Parent, DepartmentHead, LEVEL, RELATION_SHIP
from course.models import AdmissionSession

fake = Faker()


class UserFactory(DjangoModelFactory):
    """
    Factory for creating User instances with optional flags.

    Attributes:
        username (str): The generated username.
        first_name (str): The generated first name.
        last_name (str): The generated last name.
        email (str): The generated email.
        date_joined (datetime): The current date and time.
        phone (str): The generated phone number.
        address (str): The generated address.
        is_student (bool): Flag indicating if the user is a student.
        is_teacher (bool): Flag indicating if the user is a teacher.
        is_parent (bool): Flag indicating if the user is a parent.
        is_dep_head (bool): Flag indicating if the user is a department head.
    """

    class Meta:
        model = User

    username: str = LazyAttribute(lambda x: fake.user_name())
    first_name: str = LazyAttribute(lambda x: fake.first_name())
    last_name: str = LazyAttribute(lambda x: fake.last_name())
    email: str = LazyAttribute(lambda x: fake.email())
    date_joined: timezone.datetime = timezone.now()
    phone: str = LazyAttribute(lambda x: fake.phone_number())
    address: str = LazyAttribute(lambda x: fake.address())
    is_student: bool = False
    is_teacher: bool = False
    is_parent: bool = False
    is_dep_head: bool = False

    @classmethod
    def _create(cls, model_class: type, *args, **kwargs) -> User:
        """
        Create a User instance with optional flags.

        Args:
            model_class (type): The class of the model to create.

        Returns:
            User: The created User instance.
        """
        user: User = super()._create(model_class, *args, **kwargs)

        # Set the appropriate flags based on the user type
        if cls.is_student:
            user.is_student = True
        elif cls.is_parent:
            user.is_parent = True

        user.save()
        return user


class AdmissionSessionFactory(DjangoModelFactory):
    """
    Factory for creating AdmissionSession instances.

    Attributes:
        title (str): The generated admission_session title.
        summary (str): The generated summary.
    """

    class Meta:
        model = AdmissionSession

    title: str = LazyAttribute(lambda x: fake.sentence(nb_words=3))
    summary: str = LazyAttribute(lambda x: fake.text())

    @classmethod
    def _create(cls, model_class: type, *args, **kwargs) -> AdmissionSession:
        """
        Create a AdmissionSession instance using get_or_create to avoid duplicates.

        Args:
            model_class (type): The class of the model to create.

        Returns:
            AdmissionSession: The created AdmissionSession instance.
        """
        admission_session, created = AdmissionSession.objects.get_or_create(
            title=kwargs.get("title"), defaults=kwargs
        )
        return admission_session


class StudentFactory(DjangoModelFactory):
    """
    Factory for creating Student instances with associated User and AdmissionSession.

    Attributes:
        student (User): The associated User instance.
        level (str): The level of the student.
        admission_session (AdmissionSession): The associated AdmissionSession instance.
    """

    class Meta:
        model = Student

    student: User = SubFactory(UserFactory, is_student=True)
    level: str = Iterator([choice[0] for choice in LEVEL])
    admission_session: AdmissionSession = SubFactory(AdmissionSessionFactory)


class ParentFactory(DjangoModelFactory):
    """
    Factory for creating Parent instances with associated User, Student, and AdmissionSession.

    Attributes:
        user (User): The associated User instance.
        student (Student): The associated Student instance.
        first_name (str): The generated first name.
        last_name (str): The generated last name.
        phone (str): The generated phone number.
        email (str): The generated email.
        relation_ship (str): The relationship with the student.
    """

    class Meta:
        model = Parent

    user: User = SubFactory(UserFactory, is_parent=True)
    student: Student = SubFactory(StudentFactory)
    first_name: str = LazyAttribute(lambda x: fake.first_name())
    last_name: str = LazyAttribute(lambda x: fake.last_name())
    phone: str = LazyAttribute(lambda x: fake.phone_number())
    email: str = LazyAttribute(lambda x: fake.email())
    relation_ship: str = Iterator([choice[0] for choice in RELATION_SHIP])


def generate_fake_accounts_data(
    num_admission_sessions: int, num_students: int, num_parents: int
) -> None:
    """
    Generate fake data for AdmissionSessions, Students, Parents, and DepartmentHeads.

    Args:
        num_admission_sessions (int): Number of admission_sessions to generate.
        num_students (int): Number of students to generate.
        num_parents (int): Number of parents to generate.
    """
    admission_sessions: List[AdmissionSession] = AdmissionSessionFactory.create_batch(num_admission_sessions)
    students: List[Student] = StudentFactory.create_batch(num_students)
    parents: List[Parent] = ParentFactory.create_batch(num_parents)

    print(f"Created {len(admission_sessions)} admission_sessions.")
    print(f"Created {len(students)} students.")
    print(f"Created {len(parents)} parents.")
