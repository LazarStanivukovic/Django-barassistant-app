#Sofija Pavlovic 0340/2022

import json

from django.contrib.auth.models import User
from django.db.models import Avg
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404

from projekat.forms import ZaposleniForm, ArtikalForm
from projekat.models import Zaposleni, Recenzija, Artikal, TipArtikla, Polje, Sto
from projekat.views.utils import redirect_by_role

def admin(request):
    """
    **Opis**

    Prikazuje profil :model:`projekat.Zaposleni`

    **Template**

    :template:`admin/profil.html`

    :param: request: HTML request
    :return: response: HTML response
    """
    if not request.user.is_authenticated:
        return redirect('prijava')
    if request.user.zap.tip != 'A':
        return redirect_by_role(request.user)
    return render(request, 'admin/profil.html')

def zaposleni(request):
    """
    **Opis**

    Prikazuje sve :model:`projekat.Zaposleni` koji su zaposleni u restoranu
    i omogućava brisanje ili izmenu tipa zaposlenog putem AJAX-a.

    **Context**

    ``zaposleni``
        Niz :model:`projekat.Zaposleni`.

    **Template**

    :template:`admin/zaposleni.html`

    :param request: HTTP zahtev
    :return: HTTP odgovor
    """
    if not request.user.is_authenticated:
        return redirect('prijava')

    if request.user.zap.tip != 'A':
        return redirect_by_role(request.user)

    if request.method == "POST":
        id = request.POST.get('id')
        akcija = request.POST.get('akcija')
        tip = request.POST.get('tip')

        if not id:
            return JsonResponse({'status': 'error', 'message': 'ID nije prosleđen.'}, status=400)

        zap = get_object_or_404(Zaposleni, id=id)

        if akcija == 'sacuvaj':
            if tip in ['A', 'M', 'K'] and zap.tip != tip:
                zap.tip = tip
                zap.save()
                return JsonResponse({'status': 'success', 'message': 'Tip zaposlenog uspešno promenjen.'})
            else:
                return JsonResponse({'status': 'nochange', 'message': 'Nema promena.'})

        elif akcija == 'obrisi':
            zap.delete()
            return redirect('zaposleni')

    svi_zaposleni = Zaposleni.objects.all()
    zaposleni_lista = []

    for z in svi_zaposleni:
        ocena = '-'
        if z.tip == 'K':
            avg = Recenzija.objects.filter(konobar=z).aggregate(avg_ocena=Avg('ocena'))['avg_ocena']
            if avg is not None:
                ocena = round(avg, 1)

        zaposleni_lista.append({
            'id': z.id,
            'ime': z.user.first_name,
            'prezime': z.user.last_name,
            'email': z.user.email,
            'korisnicko_ime': z.user.username,
            'lozinka': z.user.password,
            'tip': z.tip,
            'ocena': ocena
        })

    return render(request, 'admin/zaposleni.html', {'zaposleni': zaposleni_lista})


def dodaj_zaposlenog(request):
    """
    **Opis**

    Prikaz i dodavanje :model:`projekat.Zaposleni`.

     **Context**

    ``zaposleni``
        Niz :model:`projekat.Zaposleni`.

    **Template**

    :template:`admin/dodaj_zaposlenog.html`

    :param: request: HTML request
    :return: response: HTML response
    """
    if not request.user.is_authenticated:
        return redirect('prijava')

    if request.user.zap.tip != 'A':
        return redirect_by_role(request.user)

    if request.method == 'POST':
        form = ZaposleniForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            user = User.objects.create_user(
                username=data['username'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                email=data['email'],
                password=data['password']
            )

            if data['tip'] == 'A':
                user.is_staff = True
                user.is_superuser = True
                user.save()
            else:
                user.is_staff = False
                user.is_superuser = False
                user.save()

            Zaposleni.objects.create(user=user, tip=data['tip'])

            return redirect('zaposleni')
    else:
        form = ZaposleniForm()

    return render(request, 'admin/dodaj_zaposlenog.html', {'form': form})
def artikli(request):
    """
    **Opis**

    Prikazuje sve :model:`projekat.Artikal` koji su u ponudi restorana.

    **Context**

    ``artikli``
        Niz :model:`projekat.Artikal`.

    **Template**

    :template:`admin/artikal.html`

    :param: request: HTML request
    :return: response: HTML response
    """
    if not request.user.is_authenticated:
        return redirect('prijava')

    if request.user.zap.tip != 'A':
        return redirect_by_role(request.user)

    if request.method == "POST":
        id = request.POST.get('id')
        if id:
            artikal = get_object_or_404(Artikal, id=id)
            artikal.delete()
            return redirect('artikli')

    artikli = Artikal.objects.all()
    artikli_lista = []
    for a in artikli:

        artikli_lista.append({
            'id': a.id,
            'naziv': a.naziv,
            'tip': a.tip_artikla,
            'cena': a.cena
        })

    return render(request, 'admin/artikal.html', {'artikli': artikli_lista})

def dodaj_artikal(request):
    """
    **Opis**

      Prikaz i dodavanje :model:`projekat.Artikal`.

      **Context**

    ``form``
        Forma za kreiranje :model:`projekat.Artikal`.

    **Template**

    :template:`admin/dodaj_artikal.html`

    :param: request: HTML request
    :return: response: HTML response
    """
    if not request.user.is_authenticated:
        return redirect('prijava')

    if request.user.zap.tip != 'A':
        return redirect_by_role(request.user)

    if request.method == 'POST':
        form = ArtikalForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            Artikal.objects.create(tip_artikla=data['tip'], naziv=data['naziv'], cena=data['cena'],kolicina_na_stanju=0)
            return redirect('artikli')
    else:
        form = ArtikalForm()

    return render(request, 'admin/dodaj_artikal.html', {'form': form})

def promeni_cenu(request):
    """
    **Opis**
    Prikaz i promena cene artikla (admin funkcionalnost).
    """
    if not request.user.is_authenticated:
        return redirect('prijava')

    if request.user.zap.tip != 'A':
        return redirect_by_role(request.user)

    artikal_id = request.GET.get('id') or request.POST.get('id')
    artikal = get_object_or_404(Artikal, id=artikal_id)

    if request.method == 'POST':
        nova_cena = request.POST.get('nova_cena', '').strip()

        if not nova_cena:
            return render(request, 'admin/promeni_cenu.html', {
                'artikal': artikal,
                'error': 'Molimo unesite novu cenu.'
            })
        artikal.cena = int(nova_cena)
        artikal.save()
        return redirect('artikli')

    return render(request, 'admin/promeni_cenu.html', {'artikal': artikal})


def tipovi_artikala(request):
    """
    **Opis**

    Prikazuje sve :model:`projekat.TipArtikla` koji su u ponudi restorana.

    **Context**

    ``artikli``
        Niz :model:`projekat.Artikal`.

    **Template**

    :template:`admin/tipovi_artikla.html`

    :param: request: HTML request
    :return: response: HTML response
    """
    if not request.user.is_authenticated:
        return redirect('prijava')

    if request.user.zap.tip != 'A':
        return redirect_by_role(request.user)

    if request.method == "POST":
        id = request.POST.get('id')
        if id:
            tip_artikla = get_object_or_404(TipArtikla, id=id)
            tip_artikla.delete()
            return redirect('tipovi_artikala')

    tipovi = TipArtikla.objects.all()
    tipovi_lista = []
    for a in tipovi:
        tipovi_lista.append({
            'id': a.id,
            'naziv': a.naziv,
        })

    return render(request, 'admin/tipovi_artikala.html', {"artikli": tipovi_lista})

def dodaj_tip_artikla(request):
    """
    **Opis**

    Prikaz i dodavanje :model:`projekat.TipArtikla`.

    **Template**

    :template:`admin/dodaj_tip_artikla.html`

    :param: request: HTML request
    :return: response: HTML response
    """
    if not request.user.is_authenticated:
        return redirect('prijava')

    if request.user.zap.tip != 'A':
        return redirect_by_role(request.user)

    if request.method == 'POST':
        naziv=request.POST.get('naziv')

        if not naziv or naziv.strip() == "":
            return render(request, 'admin/dodaj_tip_artikla.html', {'error':'Molimo unesite naziv tipa artikla'})

        TipArtikla.objects.create(naziv=naziv.strip())

        return redirect('tipovi_artikala')

    return render(request, 'admin/dodaj_tip_artikla.html')


def raspored_stolova(request):
    """
     **Opis**

        Prikazuje sve :model:`projekat.Polja` u :model:`projekat.Sto` koji su ukljuceni u raspored prostora.

        **Context**

        ``polja``
            Niz :model:`projekat.Polja`.

        **Template**

        :template:`admin/raspored_stolova.html`

        :param: request: HTML request
        :return: response: HTML response
    """
    if not request.user.is_authenticated:
        return redirect('prijava')

    if request.user.zap.tip != 'A':
        return redirect_by_role(request.user)

    if request.method == "POST":
        data = json.loads(request.body)
        cells = data.get("cells", [])

        new_coords = {(int(c["x"]), int(c["y"])) for c in cells if c.get("sto") or c.get("blocked")}

        for polje in Polje.objects.all():
            if (polje.x, polje.y) not in new_coords:
                polje.delete()

        for cell in cells:
            x = int(int(cell["x"]) // 65)
            y = int(int(cell["y"]) // 65)
            has_table = cell.get("sto", False)
            blocked = cell.get("blocked", False)

            polje, _ = Polje.objects.get_or_create(x=x, y=y)

            if has_table:
                Sto.objects.update_or_create(polje=polje)
            else:
                Sto.objects.filter(polje=polje).delete()

            if not has_table and not blocked:
                polje.delete()

        return JsonResponse({"status": "ok"})

    width, height = 10, 7
    cell_size = 65

    polja = {(p.x, p.y): p for p in Polje.objects.all()}
    stolovi = list(Sto.objects.select_related("polje").all())

    stolovi.sort(key=lambda s: (s.polje.y, s.polje.x))

    broj_map = {}
    for i, sto in enumerate(stolovi, start=1):
        broj_map[sto.polje_id] = i

    polja_data = []
    for y in range(height):
        for x in range(width):
            polje = polja.get((x, y))
            if polje:
                sto = next((s for s in stolovi if s.polje_id == polje.id), None)
                blokirano = not bool(sto)
                polja_data.append({
                    "x": x * cell_size,
                    "y": y * cell_size,
                    "blokirano": blokirano,
                    "sto_id": sto.id if sto else None,
                    "broj_stola": broj_map.get(polje.id) if sto else None
                })
            else:
                polja_data.append({
                    "x": x * cell_size,
                    "y": y * cell_size,
                    "blokirano": False,
                    "sto_id": None,
                    "broj_stola": None
                })

    return render(request, "admin/raspored_stolova.html", {"polja": polja_data})

