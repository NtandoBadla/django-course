from django.urls import path
from . import views

app_name = 'onlinecourse'

urlpatterns = [
    path('', views.index, name='index'),
    path('registration/', views.registration_request, name='registration'),
    path('login/', views.login_request, name='login'),
    path('logout/', views.logout_request, name='logout'),
    path('course/<int:course_id>/', views.course_details, name='course_details'),
    path('course/<int:course_id>/enroll/', views.enroll, name='enroll'),
    path('course/<int:course_id>/exam/', views.exam, name='exam'),
    path('course/<int:course_id>/submit/', views.submit, name='submit'),
    path('course/<int:course_id>/submission/<int:submission_id>/result/',
         views.show_exam_result, name='show_exam_result'),
]
