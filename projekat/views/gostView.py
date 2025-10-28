# Aleksa Sekulic 0021/2022


from django.shortcuts import render, redirect

from projekat.models import Artikal, Sto, Racun, Stavka, Recenzija


def pocetna(request):
    """
    **Opis**

    Prikazuje početni ekran korisnika.

    **Context**

    ``ime``
        String imena kafića.
    ``id``
        Identifikator :model:`projekat.Sto` čiji je qr kod skeniran da bi se pristupilo ovoj stranici.

    **Template**

    :template:`gost/pocetna.html`

    :param: request: HTML request
    :return: response: HTML response
    """
    return render(request, 'gost/pocetna.html', {'ime': 'The Three Carrots Pub', 'id': request.session.get('id')})

def karta_pica(request):
    """
    **Opis**

    Prikazuje sve :model:`projekat.Artikal` u ponudi.

    **Context**

    ``artikli``
        Niz :model:`projekat.Artikal`.

    **Template**

    :template:`gost/karta_pica.html`

    :param: request: HTML request
    :return: response: HTML response
    """
    artikli = Artikal.objects.all()
    return render(request, 'gost/karta_pica.html', {'artikli': artikli})

def racun_gost(request, id):
    """
    **Opis**

    Prikazuje :model:`projekat.Racun` gosta izlistavajući sve :model:`projekat.Stavka`.

    **Context**

    ``konobar``
        :model:`projekat.Zaposleni`. tipa konobar koji uslužuje dati sto.
    ``stavke``
        Niz :model:`projekat.Stavka`.
    ``ukupno``
        Ukupna suma svih :model:`projekat.Stavka`.

    **Template**

    :template:`gost/racun.html`

    :param: request: HTML request, id: identifikator :model:`projekat.Sto`
    :return: response: HTML response
    """
    konobar = None
    stavke = None
    ukupno = 0
    try:
        sto = Sto.objects.get(id=id)
        racun = Racun.objects.get(sto=sto, status='O')
        konobar = racun.konobar
        stavke = Stavka.objects.filter(racun=racun)
        for s in stavke:
            ukupno += s.cena
    except:
        pass
    return render(request, 'gost/racun.html', {'konobar': konobar, 'stavke': stavke, 'ukupno': ukupno})

def oceni_nas(request):
    """
    **Opis**

    Prikazuje ekran za ocenjivanje usluge i kreira novu :model:`projekat.Recenzija`.

    **Template**

    :template:`gost/oceni_nas.html`

    :param: request: HTML request
    :return: response: HTML response
    """
    if request.method == 'POST':
        id = request.session.get('id')
        if id:
            ocena = int(request.POST.get('ocena'))
            if ocena:
                try:
                    sto = Sto.objects.get(id=id)
                    racun = Racun.objects.get(sto=sto, status='O')
                    recenzija = Recenzija.objects.filter(racun=racun).first()
                    if recenzija:
                        recenzija.ocena = ocena
                        recenzija.save()
                    else:
                        Recenzija.objects.create(ocena=ocena, racun=racun, konobar=racun.konobar)
                except:
                    pass
        return redirect('pocetna')
    return render(request, 'gost/oceni_nas.html')

def ulaz(request, id):
    """
    **Opis**

    Služi kao ulazna tačka posle skeniranja qr koda.

    :param: request: HTML request, id: identifikator :model:`projekat.Sto`
    :return: response: HTML response
    """
    request.session['id'] = id
    return redirect('pocetna')