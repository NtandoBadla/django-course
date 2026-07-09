import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from .models import Course, Enrollment, Question, Choice, Submission

logger = logging.getLogger(__name__)


def index(request):
    courses = Course.objects.order_by('-total_enrollment')[:10]
    return render(request, 'onlinecourse/index_bootstrap.html', {'courses': courses})


def registration_request(request):
    context = {}
    if request.method == 'GET':
        return render(request, 'onlinecourse/user_registration_bootstrap.html', context)
    elif request.method == 'POST':
        username = request.POST['username']
        password = request.POST['psw']
        first_name = request.POST.get('firstname', '')
        last_name = request.POST.get('lastname', '')
        user_exists = User.objects.filter(username=username).exists()
        if not user_exists:
            user = User.objects.create_user(
                username=username, first_name=first_name,
                last_name=last_name, password=password
            )
            login(request, user)
            return redirect('onlinecourse:index')
        else:
            context['message'] = "User already exists."
            return render(request, 'onlinecourse/user_registration_bootstrap.html', context)


def login_request(request):
    context = {}
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['psw']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('onlinecourse:index')
        else:
            context['message'] = "Invalid username or password."
            return render(request, 'onlinecourse/user_login_bootstrap.html', context)
    else:
        return render(request, 'onlinecourse/user_login_bootstrap.html', context)


def logout_request(request):
    logout(request)
    return redirect('onlinecourse:index')


def check_if_enrolled(user, course):
    is_enrolled = False
    if user.id is not None:
        num_results = Enrollment.objects.filter(user=user, course=course).count()
        is_enrolled = num_results > 0
    return is_enrolled


def course_details(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    is_enrolled = check_if_enrolled(request.user, course)
    return render(request, 'onlinecourse/course_details_bootstrap.html',
                  {'course': course, 'is_enrolled': is_enrolled})


@login_required
def enroll(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    is_enrolled = check_if_enrolled(user, course)
    if not is_enrolled and user.is_authenticated:
        Enrollment.objects.create(user=user, course=course, mode='honor')
        course.total_enrollment += 1
        course.save()

    return HttpResponseRedirect(reverse('onlinecourse:course_details', args=(course.id,)))


@login_required
def exam(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    questions = course.questions.all()
    return render(request, 'onlinecourse/exam_bootstrap.html',
                  {'course': course, 'questions': questions})


@login_required
def submit(request, course_id):
    course = get_object_or_404(Course, pk=course_id)
    user = request.user

    enrollment = Enrollment.objects.get(user=user, course=course)
    submission = Submission.objects.create(enrollment=enrollment)

    selected_choice_ids = []
    for key in request.POST:
        if key.startswith('choice'):
            values = request.POST.getlist(key)
            for value in values:
                selected_choice_ids.append(int(value))

    selected_choices = Choice.objects.filter(id__in=selected_choice_ids)
    submission.choices.set(selected_choices)
    submission.save()

    return HttpResponseRedirect(
        reverse('onlinecourse:show_exam_result', args=(course.id, submission.id))
    )


def show_exam_result(request, course_id, submission_id):
    course = get_object_or_404(Course, pk=course_id)
    submission = get_object_or_404(Submission, pk=submission_id)
    selected_choice_ids = submission.choices.values_list('id', flat=True)

    questions = course.questions.all()
    total_score = 0
    total_possible = 0

    for question in questions:
        total_possible += question.question_grade
        question_selected_ids = question.choice_set.filter(
            id__in=selected_choice_ids
        ).values_list('id', flat=True)

        if question.is_get_score(question_selected_ids):
            total_score += question.question_grade

    passed = total_possible > 0 and total_score >= (total_possible * 0.8)

    context = {
        'course': course,
        'grade': total_score,
        'total_possible': total_possible,
        'passed': passed,
        'choices': submission.choices.all(),
    }
    return render(request, 'onlinecourse/exam_result_bootstrap.html', context)
