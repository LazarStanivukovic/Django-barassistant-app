#Andrej Velickov 0569/2022
from datetime import date, timedelta
from itertools import zip_longest


from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
import json

from django.utils import timezone


from projekat.models import Recenzija, Smena, Polje, Sto, Stavka, Artikal, Racun, Zaposleni
from projekat.views.adminView import artikli
from projekat.views.utils import redirect_by_role

def konobar(request):
    """
    **Opis**

    Prikazuje profil :model:`projekat.Zaposleni` ako je ulogovan i ima tip 'K'.

    **Context**

    ``prosecnaOcena``
        Prosečna ocena trenutno prijavljenog konobara.
    ``brojOcena``
        Broj ocena trenutno prijavljenog konobara.

    **Template**

    :template:`konobar/profil.html`

    :param: request: HTML request
    :return: response: HTML response ili redirect ako nije konobar
    """
    if not request.user.is_authenticated:
        return redirect('prijava')
    if request.user.zap.tip != 'K':
        return redirect_by_role(request.user)

    oceneKonobara = Recenzija.objects.filter(konobar_id = request.user.zap.id)
    brojOcena = Recenzija.objects.filter(konobar_id = request.user.zap.id).count()
    zbirOcena = 0

    for ocena in oceneKonobara:
        zbirOcena = zbirOcena + ocena.ocena

    if brojOcena != 0:
        prosecnaOcena = zbirOcena / brojOcena

    else:
        prosecnaOcena = 0

    return render(request, 'konobar/profil.html', {'prosecnaOcena': prosecnaOcena, 'brojOcena': brojOcena})

def smene(request):
    """
    **Opis**

    Prikazuje raspored :model:`projekat.Smena` za trenutnu nedelju. Svaki dan prikazuje angažovanost prijavljenog konobara po smenama.

    **Context**

    ``week_dates``
        Lista datuma za trenutnu nedelju (ponedeljak → nedelja).
    ``firstShift``
        Lista angažovanosti konobara u prvoj smeni (08:00-16:00) po danima.
    ``secondShift``
        Lista angažovanosti konobara u drugoj smeni (16:00-00:00) po danima.

    **Template**

    :template:`konobar/raspored.html`

    :param: request: HTML request
    :return: response: HTML response ili redirect ako nije konobar
    """
    if not request.user.is_authenticated:
        return redirect('prijava')
    if request.user.zap.tip != 'K':
        return redirect_by_role(request.user)

    today = date.today()
    monday = today - timedelta(days=today.weekday())
    week_dates = [monday + timedelta(days=i) for i in range(7)]

    smene = Smena.objects.filter(datum__in=week_dates)

    firstShiftDict = {day: [] for day in week_dates}
    secondShiftDict = {day: [] for day in week_dates}

    for s in smene:
        if s.broj_smene == 1 and s.konobar_id == request.user.zap.id:
            firstShiftDict[s.datum].append("X")
        elif s.broj_smene == 2 and s.konobar_id == request.user.zap.id:
            secondShiftDict[s.datum].append("X")

    firstShift = [firstShiftDict[day] for day in week_dates]
    secondShift = [secondShiftDict[day] for day in week_dates]

    return render(request, 'konobar/raspored.html', {
        'week_dates': week_dates,
        'firstShift': firstShift,
        'secondShift': secondShift
    })

def stolovi(request):
    """
     **Opis**

    Prikazuje sve :model:`projekat.Polja` u :model:`projekat.Sto` koji su ukljuceni u raspored prostora.

    **Context**

    ``polja``
        Niz :model:`projekat.Polja` sa dodatnim inoformacijama zauzetosti od strane drugog konobara (odnosi se na sto na tom polju).

    **Template**

    :template:`konobar/stolovi.html`

    :param: request: HTML request
    :return: response: HTML response ili redirect ako nije konobar
    """
    if not request.user.is_authenticated:
        return redirect('prijava')

    if request.user.zap.tip != 'K':
        return redirect_by_role(request.user)

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
                zauzet = False

                if not blokirano:
                    zauzet = False
                    racunSto = Racun.objects.filter(sto=sto.id, status="O").first()
                    if racunSto:
                        if racunSto.konobar_id != request.user.zap.id:
                            zauzet = True
                        else:
                            zauzet = False

                polja_data.append({
                    "x": x * cell_size,
                    "y": y * cell_size,
                    "blokirano": blokirano,
                    "zauzet": zauzet,
                    "sto_id": sto.id if sto else None,
                    "broj_stola": broj_map.get(polje.id) if sto else None
                })
            else:
                polja_data.append({
                    "x": x * cell_size,
                    "y": y * cell_size,
                    "blokirano": False,
                    "zauzet": False,
                    "sto_id": None,
                    "broj_stola": None
                })

    return render(request, "konobar/stolovi.html", {"polja": polja_data})

def racun(request, id):
    """
    **Opis**

    Prikazuje sve :model:`projekat.Stavka` u :model:`projekat.Racun` koji se nalaze na računu datog stola.

    **Context**

    ``konobar``
        :model:`projekat.Zaposleni`. tipa konobar koji uslužuje dati sto na datom računu.
    ``stavke``
        Niz :model:`projekat.Stavka`.
    ``id``
         :model:`projekat.Sto`. na kom je otvoren dati račun.
    ``otvoren``
        Vrednost 0 ili 1 koja govori da li za dati sto otvoren račun.

    **Template**

    :template:`konobar/racun.html`

    :param: request: HTML request, id: identifikator :model:`projekat.Sto`
    :return: response: HTML response ili redirect ako nije konobar
    """

    if not request.user.is_authenticated:
        return redirect('prijava')

    if request.user.zap.tip != 'K':
        return redirect_by_role(request.user)

    if request.method == "POST":
        id1 = request.POST.get("id")
        action = request.POST.get("action")

        if action == "close":
            racun = Racun.objects.filter(sto = id, status = "O").first()
            racunId = racun.id
            Racun.objects.filter(id = racunId).update(status = "Z")
            return redirect('racun', id)

        if action == "open":
            objektSto = Sto.objects.get(id=id)
            racun = Racun.objects.create(konobar=request.user.zap, sto=objektSto, status="O", datum_otvaranja=timezone.now().date())
            return redirect('racun', id)

        taStavka = get_object_or_404(Stavka, id=id1)

        kolicinaArtikal = taStavka.artikal.kolicina_na_stanju
        cenaArtikal = taStavka.artikal.cena

        kolicinaStavka = taStavka.kolicina
        cenaStavka = taStavka.cena


        if action == "inc":
            Stavka.objects.filter(id=id1).update(kolicina = kolicinaStavka + 1)
            Stavka.objects.filter(id=id1).update(cena=F("cena") + cenaArtikal)
            Artikal.objects.filter(id=taStavka.artikal.id).update(kolicina_na_stanju = F("kolicina_na_stanju") - 1)

        elif action == "dec":

            if kolicinaStavka == 1:
                Stavka.objects.filter(id=id1).delete()


            Stavka.objects.filter(id=id1).update(kolicina=kolicinaStavka - 1)
            Stavka.objects.filter(id=id1).update(cena=F("cena") - cenaArtikal)
            Artikal.objects.filter(id=taStavka.artikal.id).update(kolicina_na_stanju=F("kolicina_na_stanju") + 1)

        return redirect('racun', id)


    racunId = Racun.objects.filter(sto=id, status='O').first()
    if racunId is None:
        otvoren = 0
        stavke_list = []
        return render(request, "konobar/racun.html", {"stavke": stavke_list, "sto": id, "otvoren": otvoren})

    otvoren = 1
    stavke = Stavka.objects.filter(racun=racunId.id)
    stavke_list = []

    for s in stavke:

        stavke_list.append({
            'id': s.id,
            'naziv': s.artikal.naziv,
            'kolicina': s.kolicina,
            'jcena': s.artikal.cena,
            'cena': s.cena,
            'preostala_kolicina': s.artikal.kolicina_na_stanju
        })


    return render(request, "konobar/racun.html", {"stavke": stavke_list, "konobar" : request.user.username, "sto" : id, "otvoren" : otvoren})

def stavka(request, id):
    """
    **Opis**

    Prikaz i dodavanje :model:`projekat.Stavka` na otvoreni :model:`projekat.Racun` datog stola.

    **Context**

    ``artikli``
        Niz :model:`projekat.Artikal` naziva.
    ``nedovoljno``
        Vrednost 0 ili 1 koja govori da li postoji dovoljan broj artikala na stanju za trazenu porudzbinu.

     **Template**

    :template:`konobar/stavka.html`

    :param: request: HTML request, id: identifikator :model:`projekat.Sto`
    :return: response: HTML response ili redirect ako nije konobar
    """

    if not request.user.is_authenticated:
        return redirect('prijava')

    if request.user.zap.tip != 'K':
        return redirect_by_role(request.user)

    if request.method == "POST":
        racun = Racun.objects.filter(sto=id, status = "O").first()

        nazivArtikla = request.POST.get("nazivArtikla")
        kolicinaArt = request.POST.get("kolicinaArtikla")
        kolicinaArtikla = int(kolicinaArt)
        artikal = Artikal.objects.filter(naziv=nazivArtikla).first()
        dostupnaKolicina = artikal.kolicina_na_stanju

        if kolicinaArtikla > dostupnaKolicina:

            nedovoljno = "1"
            artikli = Artikal.objects.filter(kolicina_na_stanju__gt=0)
            return render(request, "konobar/stavka.html", {"artikli": artikli, "nedovoljno": nedovoljno, "dostupno": dostupnaKolicina})

        stavkaRacuna = Stavka.objects.filter(racun=racun.id, artikal=artikal.id).first()

        if not stavkaRacuna is None:
            stavkaRacuna.kolicina = F('kolicina') + kolicinaArtikla
            stavkaRacuna.save()
            return redirect('racun', id)

        cenaArtikla = artikal.cena
        cenaStavke = cenaArtikla * kolicinaArtikla

        Stavka.objects.create(racun=racun, artikal=artikal, kolicina=kolicinaArtikla, cena=cenaStavke)
        Artikal.objects.filter(naziv=nazivArtikla).update(kolicina_na_stanju=F("kolicina_na_stanju") - kolicinaArtikla)
        return redirect('racun', id)

    artikli = Artikal.objects.filter(kolicina_na_stanju__gt=0)
    nedovoljno = "0"
    return render(request, "konobar/stavka.html", {"artikli": artikli, "nedovoljno": nedovoljno})