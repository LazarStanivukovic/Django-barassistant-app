#Aleksa Sekulic 0021/2022


import secrets
import string

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.shortcuts import render, redirect

from projekat.views.utils import redirect_by_role


def prijava(request):
    """
    **Opis**

    Obrađuje prijavu korisnika na sistem.

    **Context**

    ``error``
        String poruka o grešci pri prijavi.

    **Template**

    :template:`prijava/prijava.html`

    :param: request: HTML request
    :return: response: HTML response
    """
    if request.user.is_authenticated:
        return redirect_by_role(request.user)
    error = ''
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            return redirect_by_role(request.user)
        error = 'Pogrešni kredencijali'
    return render(request, 'prijava/prijava.html', context={'error': error})

def odjava(request):
    """
    **Opis**

    Obrađuje odjavu korisnika sa sistema.

    :param: request: HTML request
    :return: response: HTML response
    """
    if request.user.is_authenticated:
        logout(request)
    return redirect('prijava')

def restauracija(request):
    """
    **Opis**

    Ažurira lozinku korisnika novonapravljenom lozinkom i šalje mu je na email.

    **Context**

    ``msg``
        String poruka o grešci ili uspehu pri restauraciji.
    ``success``
        Bool indikator o tome da li je restauracija uspela ili ne.

    **Template**

    :template:`prijava/restauracija.html`

    :param: request: HTML request
    :return: response: HTML response
    """
    if request.user.is_authenticated:
        return redirect_by_role(request.user)
    msg = ''
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            reset_password(user)
            msg = 'Lozinka poslata'
        except:
            msg = 'Nepostojeća email adresa'
            return render(request, 'prijava/restauracija.html', context={'msg': msg, 'success': False})
    return render(request, 'prijava/restauracija.html', context={'msg': msg, 'success': True})

def reset_password(user):
    """
    **Opis**

    Generiše novu jaku lozinku i šalje je na email korisniku.

    :param: user: User
    :return: None
    """
    alphabet = string.ascii_letters + string.digits
    new_password = ''.join(secrets.choice(alphabet) for _ in range(10))

    user.set_password(new_password)
    user.save()

    send_mail(
        subject='Restauracija lozinke',
        message=(
            f'Pozdrav {user.username},\n\n'
            f'Vaša nova lozinka je: {new_password}\n\n'
            f'Želimo Vam ugodan ostatak dana,\n'
            f'BarAssistant tim.'
        ),
        from_email='aleksa.se2003@gmail.com',
        recipient_list=[user.email],
        fail_silently=False,
    )
