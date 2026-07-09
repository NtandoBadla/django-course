import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib.auth import login, logout, authenticate
from .models import Course, Enrollment, Question, Choice, Submission

logger = logging.getLogger(__name__)


def registration_request(request):
    pass


def login_request(request):
    pass


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
    return render(request, 'onlinecourse/course_details_bootstrap.html', {'course': course})


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

    for question in questions:
        question_selected_ids = question.choice_set.filter(
            id__in=selected_choice_ids
        ).values_list('id', flat=True)

        if question.is_get_score(question_selected_ids):
            total_score += question.question_grade

    context = {
        'course': course,
        'grade': total_score,
        'choices': submission.choices.all(),
    }
    return render(request, 'onlinecourse/exam_result_bootstrap.html', context)
