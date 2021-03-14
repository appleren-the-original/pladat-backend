from django.urls import path

from pladat.api import views 
from rest_framework_simplejwt import views as jwt_views

from .views_student import (
    StudentListView, student_detail_view, student_update_view,
    student_star_view,
)
from .views_employer import (
    EmployerListView, employer_detail_view,
    employer_placement_list_view, employer_update_view,
)
from .views_placement import (
    PlacementListView, placement_create_view, placement_detail_view,
    placement_application_list_view, placement_update_view,
    placement_apply_view, placement_star_view,
)
from .views_other import (
    index_view, RegistrationAPIView, LoginAPIView,
    SkillListView, CategoryListView,
)


app_name = "pladat"
urlpatterns = [
    path("" , index_view, name="index"),
    
    path("students/", StudentListView.as_view(), name="student_list"),
    path("student/<pk>/" , student_detail_view, name="student_detail"),
    path("student/<pk>/update", student_update_view, name="student_update"),
    path("student/<pk>/star", student_star_view, name="student_star"),

    path("employers/", EmployerListView.as_view(), name="employer_list"),
    path("employer/<pk>/" , employer_detail_view, name="employer_detail"),
    path("employer/<pk>/placements", employer_placement_list_view, name="employer_placement_list"),
    path("employer/<pk>/update", employer_update_view, name="employer_update"),

    path("placements/", PlacementListView.as_view(), name="placement_list"),
    path("placements/create", placement_create_view, name="placement_create"),
    path("placement/<pk>/" , placement_detail_view, name="placement_detail"),
    path("placement/<pk>/applications/", placement_application_list_view, name="placement_applications"),
    path("placement/<pk>/update", placement_update_view, name="placement_update"),
    path("placement/<pk>/apply", placement_apply_view, name="placement_apply"),
    path("placement/<pk>/star", placement_star_view, name="placement_star"),

    # authentication - jwt
    path('signup/', RegistrationAPIView.as_view()),
    path('login/', LoginAPIView.as_view()),

    # other
    path("skills/", SkillListView.as_view(), name="skill_list"),
    path("categories/", CategoryListView.as_view(), name="category_list"),
]
