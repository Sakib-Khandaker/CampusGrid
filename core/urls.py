from django.urls import path

from .views import (
    home_view,
    post_add,
    edit_post,
    delete_post,
    session_list_view,
    session_add_view,
    session_update_view,
    session_delete_view,
    semester_list_view,
    semester_add_view,
    semester_update_view,
    semester_delete_view,
    dashboard_view,
    add_notice,
    delete_notice,

    # 🔥 NEW VIEWS
    notices_view,
    curriculum_view,
    edit_notice,

)


urlpatterns = [
    path("", home_view, name="home"),

    path("add_item/", post_add, name="add_item"),
    path("item/<int:pk>/edit/", edit_post, name="edit_post"),
    path("item/<int:pk>/delete/", delete_post, name="delete_post"),

    path("session/", session_list_view, name="session_list"),
    path("session/add/", session_add_view, name="add_session"),
    path("session/<int:pk>/edit/", session_update_view, name="edit_session"),
    path("session/<int:pk>/delete/", session_delete_view, name="delete_session"),

    path("semester/", semester_list_view, name="semester_list"),
    path("semester/add/", semester_add_view, name="add_semester"),
    path("semester/<int:pk>/edit/", semester_update_view, name="edit_semester"),
    path("semester/<int:pk>/delete/", semester_delete_view, name="delete_semester"),

    path("dashboard/", dashboard_view, name="dashboard"),

    path("notices/", notices_view, name="notices"),
    path("notices/add/", add_notice, name="add_notice"),  # 🔥 REQUIRED

    path("curriculum/", curriculum_view, name="curriculum"),
    path("notices/<int:pk>/edit/", edit_notice, name="edit_notice"),
    path("notices/<int:pk>/delete/", delete_notice, name="delete_notice"),
]