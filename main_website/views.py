from django.shortcuts import render, redirect
from .models import Student, Grades, Course, Department, User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from datetime import timedelta
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q


def admin_required(view_func):
    def check_admin(user):
        return user.is_authenticated and user.role == User.Role.ADMIN

    def decorator(request, *args, **kwargs):
        if check_admin(request.user):
            return view_func(request, *args, **kwargs)
        else:
            return redirect('home')  # Redirect to the home page

    return decorator


def student_required(view_func):
    def check_student(user):
        return user.is_authenticated and user.role == User.Role.STUDENT

    def decorator(request, *args, **kwargs):
        if check_student(request.user):
            return view_func(request, *args, **kwargs)
        else:
            return redirect('home')  # Redirect to the home page

    return decorator


def home(request):
    return render(request, 'main_website/home.html')


def index(request):
    return render(request, 'main_website/websites_navigation.html')


def about(request):
    return render(request, 'main_website/about.html')


@login_required(login_url='home')
def profile(request):
    return render(request, 'main_website/profile.html')


def loginStudent(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        # messages.clear(request)
        id = request.POST.get('id')
        password = request.POST.get('pass')
        remember = request.POST.get('remember')

        try:
            student = Student.objects.get(stud_id=id)
        except:
            messages.error(request, 'Credentials are not valid')
            return redirect('login_student')

        user = authenticate(request, username=student.username, password=password)

        if user is not None:
            login(request, user)

            if remember == 'on':
                request.session.set_expiry(timedelta(days=365).total_seconds())
            else:
                request.session.set_expiry(0)

            return redirect('home')
        else:
            messages.error(request, 'Credentials are not valid')
            return redirect('login_student')

    return render(request, 'main_website/login.html')


def loginAdmin(request):
    login_type = 'admin'
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('pass')
        remember = request.POST.get('remember')
        admin = authenticate(request, username=username, password=password)

        # print(remember)
        if admin is not None:
            login(request, admin)
            print(remember)

            if remember == 'on':
                request.session.set_expiry(timedelta(days=365).total_seconds())
            else:
                request.session.set_expiry(0)

            return redirect('home')
        else:
            # if username is not None and password is not None:
            messages.error(request, 'Credentials are not valid')
            return redirect('login_admin')

    context = {'login_type': login_type}
    return render(request, 'main_website/login.html', context)


def logoutPage(request):
    if not request.user.is_authenticated:
        pass
    else:
        logout(request)
    return redirect('home')


@login_required(login_url='login_student')
@student_required
def registered_courses(request):
    grades = Grades.objects.filter(student_id=request.user.student.stud_id)

    context = {
        'grades': grades
    }
    return render(request, 'main_website/registered_courses.html', context)


@login_required(login_url='login_admin')
@admin_required
def search_students(request):
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        if form_type == 'delete-form':
            delete_id = request.POST.get('delete')
            try:
                student = Student.objects.get(stud_id=delete_id)
                student.delete()
            except Student.DoesNotExist:
                pass
    students = Student.objects.all()
    search = ''
    if request.method == 'POST':
        priority = request.POST.get('priority')
        search = request.POST.get('keyword')

        if search:
            deps = Department.objects.filter(name=search)
            students = students.filter(
                (Q(name__icontains=search) | Q(department_id__in=deps.values_list('id', flat=True))) & Q(is_active=True)
            )

        if priority == 'name':
            students = students.order_by('name')
        elif priority == 'stud_id':
            students = students.order_by('stud_id')

    departments = []
    for student in students:
        department = Department.objects.get(id=student.department_id)
        departments.append(department.name)

    context = {
        'students_departments': zip(students, departments),
        'search': search,
    }
    return render(request, 'main_website/search.html', context)


@login_required(login_url='login_admin')
@admin_required
def add_course(request):
    departments = Department.objects.all()
    context = {
        'departments': departments
    }

    if request.method == 'POST':
        name = request.POST.get('name')
        course_id = request.POST.get('ID')
        number_of_hours = request.POST.get('course Hours')
        lecture_day = request.POST.get('lDay')
        hall_number = request.POST.get('hallNumber')
        department_id = request.POST.get('department')
        try:
            Course.objects.get(course_id=course_id)
            messages.error(request, 'Course ID already exists')
            return render(request, 'main_website/add_course.html', context)
        except ObjectDoesNotExist:
            pass
        department = Department.objects.get(id=department_id)
        Course.objects.create(name=name, course_id=course_id, department=department,
                              number_of_hours=number_of_hours, lecture_day=lecture_day,
                              hall_number=hall_number)
        return redirect('home')

    return render(request, 'main_website/add_course.html', context)


@login_required(login_url='login_admin')
@admin_required
def edit_student(request):
    id = request.POST.get('edit')
    student = Student.objects.get(stud_id=id)

    takenCourses = Grades.objects.filter(student_id=id, final_grade__isnull=True)
    allCourses = Course.objects.filter(department=student.department)
    nCourses = takenCourses.count()
    context = {
        'student': student,
        'takenCourses': takenCourses,
        'courses': allCourses,
        'n': nCourses,
    }

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'update':
            print("REST")
            sID = request.POST.get('student id')
            # sID hasnot changed
            name = request.POST.get('student_name')
            username = request.POST.get('username')
            email = request.POST.get('email')

            date_of_birth = request.POST.get('dateOfBirth')
            status = request.POST.get('status')
            university = request.POST.get('university')
            gender = request.POST.get('gender')
            department_id = request.POST.get('department')
            print(department_id)
            department = Department.objects.get(id=department_id)
            course1_ID = request.POST.get('course1')
            course2_ID = request.POST.get('course2')
            course3_ID = request.POST.get('course3')

            if id == sID:

                student = Student.objects.get(stud_id=sID)

                student.name = name
                student.username = username
                student.email = email
                student.date_of_birth = date_of_birth
                student.is_active = status
                student.university = university
                student.gender = gender
                student.save()
                if takenCourses.count() > 0:
                    Grades.objects.filter(student_id=id).delete()

                Grades.objects.create(student_id=sID, course_id=course1_ID)
                Grades.objects.create(student_id=sID, course_id=course2_ID)
                Grades.objects.create(student_id=sID, course_id=course3_ID)

                return redirect('search_students')
            else:
                Grades.objects.filter(student_id=id).delete()
                student.stud_id = sID
                student.name = name
                student.username = username
                student.email = email
                student.date_of_birth = date_of_birth
                student.is_active = status
                student.university = university
                student.gender = gender
                student.save()

                Grades.objects.create(student_id=sID, course_id=course1_ID)
                Grades.objects.create(student_id=sID, course_id=course2_ID)
                Grades.objects.create(student_id=sID, course_id=course3_ID)
                return redirect('search_students')

    return render(request, 'main_website/edit_student.html', context)


def error_404(request, exception):
    return render(request, 'main_website/404.html', status=404)


@login_required(login_url='login_student')
@student_required
def register_in_courses(request):
    # when clicking on the save button
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        course1_id = request.POST.get('course1')
        course2_id = request.POST.get('course2')
        course3_id = request.POST.get('course3')
        # retrieve the student

        student = Student.objects.get(user=request.user)
        Grades.objects.filter(student=student).delete()

        # retrieve the selected courses
        course1 = Course.objects.get(course_id=course1_id)
        course2 = Course.objects.get(course_id=course2_id)
        course3 = Course.objects.get(course_id=course3_id)

        Grades.objects.create(student=student, course=course1)
        Grades.objects.create(student=student, course=course2)
        Grades.objects.create(student=student, course=course3)

        return redirect('home')

    else:
        student_id = request.POST.get('student_id')
        student = Student.objects.get(user=request.user)
        department_courses = Course.objects.filter(department=student.department)

        context = {
            'student': student,
            'department_courses': department_courses,
        }
    return render(request, 'main_website/register_in_courses.html', context)


@login_required(login_url='login_admin')
@staff_member_required
def add_student(request):
    if request.method == 'POST':
        name = request.POST.get('student name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        stud_id = request.POST.get('student id')
        password = request.POST.get('password')
        date_of_birth = request.POST.get('dateOfBirth')
        department_id = request.POST.get('department')
        status = request.POST.get('status')

        university = request.POST.get('university')
        gender = request.POST.get('gender')

        departments = Department.objects.all()
        context = {
            'departments': departments
        }
        # Check if username and email already exist
        try:
            Student.objects.get(username=username)
            messages.error(request, 'Username already exists')
            return render(request, 'main_website/add_student.html', context)
        except ObjectDoesNotExist:
            pass

        try:
            Student.objects.get(email=email)
            messages.error(request, 'Email already exists')
            return render(request, 'main_website/add_student.html', context)
        except ObjectDoesNotExist:
            pass

        # Check if student ID already exists
        try:
            Student.objects.get(stud_id=stud_id)
            messages.error(request, 'Student ID already exists')
            return render(request, 'main_website/add_student.html', context)
        except ObjectDoesNotExist:
            pass

            department = Department.objects.get(id=department_id)

            Student.objects.create_user(name=name, username=username, email=email, stud_id=stud_id,
                                        password=password,
                                        date_of_birth=date_of_birth, department=department,
                                        is_active=status, university=university, gender=gender)

        return render(request, 'main_website/add_student.html', context)

    else:
        departments = Department.objects.all()
        context = {
            'departments': departments
        }
        return render(request, 'main_website/add_student.html', context)
