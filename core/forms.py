from django import forms
from .models import NewsAndEvents, Session, Semester, SEMESTER, Notice


# ########################################################
# NEWS & EVENTS FORM
# ########################################################
class NewsAndEventsForm(forms.ModelForm):
    class Meta:
        model = NewsAndEvents
        fields = ("title", "summary", "posted_as")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["title"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Enter title"
        })

        self.fields["summary"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Enter summary"
        })

        self.fields["posted_as"].widget.attrs.update({
            "class": "form-control"
        })


# ########################################################
# NOTICE FORM (FINAL FIXED VERSION)
# ########################################################
class NoticeForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = (
            "title",
            "content",
            "image",
            "document",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["title"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Notice title"
        })

        self.fields["content"].widget.attrs.update({
            "class": "form-control",
            "placeholder": "Write notice details..."
        })

        # File fields (important: keep simple for proper upload UI)
        self.fields["image"].widget.attrs.update({
            "class": "form-control"
        })

        self.fields["document"].widget.attrs.update({
            "class": "form-control"
        })


# ########################################################
# SESSION FORM
# ########################################################
class SessionForm(forms.ModelForm):
    next_session_begins = forms.DateField(
        widget=forms.TextInput(attrs={"type": "date"}),
        required=True,
    )

    class Meta:
        model = Session
        fields = ["session", "is_current_session", "next_session_begins"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["session"].widget.attrs.update({
            "class": "form-control"
        })

        self.fields["is_current_session"].widget.attrs.update({
            "class": "form-check-input"
        })


# ########################################################
# SEMESTER FORM
# ########################################################
class SemesterForm(forms.ModelForm):
    semester = forms.CharField(
        widget=forms.Select(
            choices=SEMESTER,
            attrs={"class": "form-control"},
        ),
        label="Semester",
    )

    is_current_semester = forms.CharField(
        widget=forms.Select(
            choices=((True, "Yes"), (False, "No")),
            attrs={"class": "form-control"},
        ),
        label="Is current semester?",
    )

    session = forms.ModelChoiceField(
        queryset=Session.objects.all(),
        widget=forms.Select(attrs={"class": "form-control"}),
        required=True,
    )

    next_semester_begins = forms.DateField(
        widget=forms.TextInput(attrs={
            "type": "date",
            "class": "form-control",
        }),
        required=True,
    )

    class Meta:
        model = Semester
        fields = [
            "semester",
            "is_current_semester",
            "session",
            "next_semester_begins"
        ]