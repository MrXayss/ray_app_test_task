from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import auth
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from .models import Person
from django.contrib.auth.decorators import login_required
import asyncio
import aiohttp
import requests
from ray_app_test_task.settings import API_KEY


def login(request, user):
    """
    Отображает страницу входа в систему.
    """
    return render(request, 'login.html')


@csrf_exempt
@login_required
def add_data(request):
    """
    Добавляет новую запись в базу данных при получении POST-запроса.
    В противном случае отображает страницу добавления данных.
    """
    if request.method == 'POST':
        print(request, request.POST)
        print(request.POST["birth"])
        new_entry = Person(name=request.POST["name"], age=request.POST["age"],
                           birth=request.POST["birth"], place_birth=request.POST["place_birth"])
        new_entry.save()
        return redirect('show_info')
    return render(request, 'add.html')


@login_required
def show_info(request):
    """
    Отображает информацию о всех людях в базе данных и текущую погоду в Сургуте.
    """
    persons = Person.objects.all()
    response = requests.get(
        f'http://api.openweathermap.org/data/2.5/weather?q=Surgut&appid={API_KEY}&units=metric')
    data = response.json()
    weather = {
        'city': data['name'],
        'temperature': data['main']['temp'],
        'description': data['weather'][0]['description'],
    }
    template = loader.get_template('main.html')
    context = {
        'data': persons,
        'weather': weather
    }
    return HttpResponse(template.render(context, request))


@login_required
def edit(request, id):
    """
    Обновляет запись в базе данных с указанным идентификатором при получении POST-запроса.
    В противном случае отображает страницу редактирования для этой записи.
    """
    if request.method == 'POST':
        record = Person.objects.filter(id=id).update(
            name=request.POST["name"],
            age=request.POST["age"],
            birth=request.POST["birth"],
            place_birth=request.POST["place_birth"]
        )
        return redirect('show_info')
    record = Person.objects.get(id=id)
    template = loader.get_template('edit.html')
    context = {
        'data': record
    }
    return HttpResponse(template.render(context, request))


@login_required
def delete(request, id):
    """
    Удаляет запись в базе данных с указанным идентификатором и перенаправляет на страницу с информацией.
    """
    Person.objects.get(id=id).delete()
    return redirect('show_info')


@csrf_exempt
def login_view(request):
    """
    Аутентифицирует пользователя и перенаправляет на страницу с информацией при получении POST-запроса.
    В противном случае отображает страницу входа в систему.
    """
    if request.user.is_authenticated:
        return redirect('show_info')
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(request, username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return redirect('show_info')
        else:
            return render(request, 'login.html', {'error': 'Неверное имя пользователя или пароль'})
    else:
        return render(request, 'login.html')


@csrf_exempt
def register(request):
    """
    Регистрирует нового пользователя и перенаправляет на главную страницу при получении POST-запроса.
    В противном случае отображает страницу регистрации.
    """
    if request.user.is_authenticated:
        return redirect(show_info)
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth.login(request, user)
            return redirect('/')
    else:
        form = UserCreationForm()
    return render(request, 'register.html', {'form': form})


def logout(request):
    """
    Выходит из системы и перенаправляет на страницу входа в систему.
    """
    auth.logout(request)
    return redirect('login')


async def download_large_file(request, url, filename):
    """
    Асинхронно загружает большой файл по указанному URL и сохраняет его под указанным именем файла.
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=2400) as resp:
            with open(filename, 'wb') as fd:
                while True:
                    chunk = await resp.content.read(1024)
                    if not chunk:
                        break
                    fd.write(chunk)
    return FileResponse(open(filename, 'rb'))


@login_required
def download(request):
    """
    Запускает асинхронную загрузку большого файла и возвращает его в качестве ответа.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(download_large_file(
        request, 'https://www.vita-control.ru/files-vitafs.tar.gz', 'files-vitafs.tar.gz'))
    return result
