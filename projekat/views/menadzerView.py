# Lazar Stanivukovic 0590/2022
import base64
import json
from datetime import datetime, timedelta, date
from io import BytesIO
import socket
from django.utils import timezone
import qrcode
from django.http import JsonResponse
from django.shortcuts import render, redirect
from projekat.models import Artikal, TipArtikla, Stavka, Sto, Dostava, Rezervacija, Smena, Zaposleni, Racun
from projekat.views.utils import redirect_by_role

def menadzer(request):
    """
    **Opis**

    Prikazuje profil :model:`projekat.Zaposleni` ako je ulogovan i ima tip 'M'.

    **Template**

    :template:`menadzer/profil.html`

    :param: request: HTML request
    :return: response: HTML response ili redirect ako nije menadžer
    """
    if not request.user.is_authenticated:
        return redirect('prijava')
    if request.user.zap.tip != 'M':
        return redirect_by_role(request.user)
    return render(request, 'menadzer/profil.html')

def dostave(request):
    """
    **Opis**

    Prikazuje sve :model:`projekat.Dostava` sa statusom "U TOKU"
    i omogućava ažuriranje statusa preko AJAX POST zahteva.

    **Context**

    ``dostave``
        Lista :model:`projekat.Dostava` sa statusom "U TOKU".

    **Template**

    :template:`menadzer/dostava.html`

    :param: request: HTML request
    :return: response: HTML response ili redirect ako nije menadžer
    """
    if not request.user.is_authenticated:
        return redirect('prijava')
    if request.user.zap.tip != 'M':
        return redirect_by_role(request.user)

    if request.method == "POST" and request.headers.get("X-Requested-With") == "XMLHttpRequest":
        try:
            data = json.loads(request.body)
            dostava_id = data.get("id")
            new_status = data.get("status")

            d = Dostava.objects.get(id=dostava_id)
            d.status = new_status
            d.save()

            if new_status == "REALIZOVANA":
                artikal = d.artikal
                artikal.kolicina_na_stanju += d.kolicina
                artikal.save()

            return JsonResponse({"success": True})
        except Dostava.DoesNotExist:
            return JsonResponse({"error": "Dostava ne postoji"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    aktivne_dostave = Dostava.objects.filter(status="U TOKU")

    return render(request, 'menadzer/dostava.html', {
        'dostave': aktivne_dostave
    })
def dodaj_dostavu(request):
    """
    **Opis**

    Omogućava :model:`projekat.Zaposleni` da kreira novu :model:`projekat.Dostava`.

    **Context**

    ``artikli``
        Lista svih :model:`projekat.Artikal`.
    ``error``
        Poruka o grešci ako izabrani :model:`projekat.Artikal` ne postoji.

    **Template**

    :template:`menadzer/napravi_dostavu.html`

    :param: request: HTML request
    :return: response: HTML response ili redirect na stranicu dostava nakon kreiranja
    """
    if not request.user.is_authenticated:
        return redirect('prijava')
    if request.user.zap.tip != 'M':
        return redirect_by_role(request.user)

    if request.method == 'POST':
        artikal_id = request.POST.get('artikal')
        kolicina = request.POST.get('kolicina')

        try:
            artikal = Artikal.objects.get(id=artikal_id)
        except Artikal.DoesNotExist:
            return render(request, 'menadzer/napravi_dostavu.html', {
                'artikli': Artikal.objects.all(),
                'error': 'Izabrani artikal ne postoji.'
            })

        Dostava.objects.create(
            artikal=artikal,
            kolicina=kolicina,
            status="U TOKU"
        )
        return redirect('dostave')

    artikli = Artikal.objects.all()
    return render(request, 'menadzer/napravi_dostavu.html', {'artikli': artikli})

def rezervacije(request):
    """
    **Opis**

    Prikazuje sve :model:`projekat.Rezervacija` sa statusom "U TOKU". Takođe obrađuje AJAX POST za ažuriranje statusa.

    **Context**

    ``rezervacije``
        Lista :model:`projekat.Rezervacija` sa statusom "U TOKU".

    **Template**

    :template:`menadzer/rezervacija.html`

    :param: request: HTML request
    :return: response: HTML response ili JsonResponse za AJAX
    """
    if not request.user.is_authenticated:
        return redirect('prijava')
    if request.user.zap.tip != 'M':
        return redirect_by_role(request.user)
    if request.method == "POST":
        rezervacija_id = request.POST.get('id')
        new_status = request.POST.get('status')
        try:
            rez = Rezervacija.objects.get(id=rezervacija_id)
            rez.status = new_status
            rez.save()
        except Rezervacija.DoesNotExist:
            pass
        return redirect('rezervacije')

    aktivne_rezervacije = Rezervacija.objects.filter(status="U TOKU")

    return render(request, 'menadzer/rezervacija.html', {
        'rezervacije': aktivne_rezervacije
    })

def dodaj_rezervaciju(request):
    """
    **Opis**

    Omogućava :model:`projekat.Zaposleni` da kreira novu :model:`projekat.Rezervacija` i proverava preklapanja ±3h za isti :model:`projekat.Sto`.

    **Context**

    ``stolovi``
        Lista svih :model:`projekat.Sto`.
    ``error``
        Poruka o grešci ako sto ne postoji ili je već rezervisan.

    **Template**

    :template:`menadzer/napravi_rezervaciju.html`

    :param: request: HTML request
    :return: response: HTML response ili redirect na rezervacije nakon uspešnog dodavanja
    """
    if not request.user.is_authenticated:
        return redirect('prijava')
    if request.user.zap.tip != 'M':
        return redirect_by_role(request.user)

    if request.method == 'POST':
        sto_id = request.POST.get('sto')
        datum_vreme = request.POST.get('datum_vreme')
        ime = request.POST.get('ime')
        try:
            sto = Sto.objects.get(id=sto_id)
        except Sto.DoesNotExist:
            return render(request, 'menadzer/napravi_rezervaciju.html', {
                'stolovi': Sto.objects.all(),
                'error': 'Izabrani sto ne postoji.',
                'now': timezone.now(),
            })

        try:
            naive_datetime = datetime.fromisoformat(datum_vreme)
            rezervacija_vreme = timezone.make_aware(naive_datetime)
        except Exception:
            return render(request, 'menadzer/napravi_rezervaciju.html', {
                'stolovi': Sto.objects.all(),
                'error': 'Neispravan format datuma i vremena.',
                'now': timezone.now(),
            })

        start_window = rezervacija_vreme - timedelta(hours=3)
        end_window = rezervacija_vreme + timedelta(hours=3)

        overlap = Rezervacija.objects.filter(
            sto=sto,
            datum_vreme__gte=start_window,
            datum_vreme__lte=end_window,
            status="U TOKU"
        ).exists()

        if overlap:
            return render(request, 'menadzer/napravi_rezervaciju.html', {
                'stolovi': Sto.objects.all(),
                'error': f"Sto {sto.id} je već rezervisan unutar 3 sata od izabranog vremena.",
                'now': timezone.now(),
            })

        Rezervacija.objects.create(
            sto=sto,
            datum_vreme=rezervacija_vreme,
            ime=ime,
            status="U TOKU"
        )

        return redirect('rezervacije')

    return render(request, 'menadzer/napravi_rezervaciju.html', {
        'stolovi': Sto.objects.all(),
        'now': timezone.now(),
    })

def raspored_po_smenama(request):
    """
    **Opis**

    Prikazuje raspored :model:`projekat.Smena` za trenutnu nedelju. Svaki dan prikazuje :model:`projekat.Zaposleni` po :model:`projekat.Smena`.

    **Context**

    ``week_dates``
        Lista datuma za trenutnu nedelju (ponedeljak → nedelja).
    ``firstShift``
        Lista lista :model:`projekat.Zaposleni` u prvoj :model:`projekat.Smena` (08:00-16:00) po danima.
    ``secondShift``
        Lista lista :model:`projekat.Zaposleni` u drugoj :model:`projekat.Smena` (16:00-00:00) po danima.

    **Template**

    :template:`menadzer/raspored.html`

    :param: request: HTML request
    :return: response: HTML response ili redirect ako nije menadžer
    """
    if not request.user.is_authenticated:
        return redirect('prijava')
    if request.user.zap.tip != 'M':
        return redirect_by_role(request.user)
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    week_dates = [monday + timedelta(days=i) for i in range(7)]
    smene = Smena.objects.filter(datum__in=week_dates)

    firstShiftDict = {day: [] for day in week_dates}
    secondShiftDict = {day: [] for day in week_dates}

    for s in smene:
        name = s.konobar.user.get_full_name()
        if s.broj_smene == 1:
            firstShiftDict[s.datum].append(name)
        elif s.broj_smene == 2:
            secondShiftDict[s.datum].append(name)

    firstShift = [firstShiftDict[day] for day in week_dates]
    secondShift = [secondShiftDict[day] for day in week_dates]

    return render(request, 'menadzer/raspored.html', {
        'week_dates': week_dates,
        'firstShift': firstShift,
        'secondShift': secondShift
    })

def dodaj_raspored_po_smenama(request):
    """
    **Opis**

    Prikazuje formu za kreiranje rasporeda :model:`projekat.Smena` za sledeću nedelju.
    Omogućava pregled postojećih :model:`projekat.Zaposleni` po :model:`projekat.Smena` i dodavanje novih.

    **Context**

    ``shifts``
        Lista stringova naziva :model:`projekat.Smena`.
    ``week_dates``
        Lista datuma sledeće nedelje (ponedeljak → nedelja).
    ``firstShift``
        Lista lista :model:`projekat.Zaposleni` u prvoj :model:`projekat.Smena` (08:00-16:00) po danima.
    ``secondShift``
        Lista lista :model:`projekat.Zaposleni` u drugoj :model:`projekat.Smena` (16:00-00:00) po danima.
    ``week_data_first``
        Lista tuple (datum, lista :model:`projekat.Zaposleni` prve :model:`projekat.Smena`) za lakše iteriranje u template-u.
    ``week_data_second``
        Lista tuple (datum, lista :model:`projekat.Zaposleni` druge :model:`projekat.Smena`) za template.

    **Template**

    :template:`menadzer/napravi_raspored.html`

    :param: request: HTML request
    :return: response: HTML response ili redirect ako nije menadžer
    """
    if not request.user.is_authenticated:
        return redirect('prijava')
    if request.user.zap.tip != 'M':
        return redirect_by_role(request.user)

    shifts = ["08:00h - 16:00h", "16:00h - 00:00h"]
    today = date.today()
    next_monday = today + timedelta(days=(7 - today.weekday()))
    week_dates = [next_monday + timedelta(days=i) for i in range(7)]
    smene = Smena.objects.filter(datum__in=week_dates)

    firstShiftDict = {day: [] for day in week_dates}  # 08:00 - 16:00
    secondShiftDict = {day: [] for day in week_dates}  # 16:00 - 00:00

    for s in smene:
        name = s.konobar.user.get_full_name()
        if s.broj_smene == 1:
            firstShiftDict[s.datum].append(name)
        elif s.broj_smene == 2:
            secondShiftDict[s.datum].append(name)

    firstShift = [firstShiftDict[day] for day in week_dates]
    secondShift = [secondShiftDict[day] for day in week_dates]

    week_data_first = list(zip(week_dates, firstShift))
    week_data_second = list(zip(week_dates, secondShift))
    return render(request, 'menadzer/napravi_raspored.html', {
        'shifts': shifts,
        'week_dates': week_dates,
        'firstShift': firstShift,
        'secondShift': secondShift,
        'week_data_first': week_data_first,
        'week_data_second': week_data_second
    })
def dodaj_konobara(request):
    """
    **Opis**

    Omogućava dodavanje :model:`projekat.Zaposleni` u određenu :model:`projekat.Smena` za određeni datum.
    Prikazuje dostupne :model:`projekat.Zaposleni` i već dodeljene.

    **Context**

    ``date``
        Datum :model:`projekat.Smena`.
    ``shift``
        Broj :model:`projekat.Smena` (1 ili 2).
    ``assigned_konobari``
        Lista :model:`projekat.Zaposleni` koji su već dodeljeni toj :model:`projekat.Smena`.
    ``available_konobari``
        Lista :model:`projekat.Zaposleni` koji nisu dodeljeni toj :model:`projekat.Smena`.

    **Template**

    :template:`menadzer/dodaj_konobara.html`

    :param: request: HTML request
    :return: response: HTML response ili update rasporeda nakon POST
    """
    if not request.user.is_authenticated:
        return redirect('prijava')
    if request.user.zap.tip != 'M':
        return redirect_by_role(request.user)

    date_str = request.GET.get('date')
    shift = request.GET.get('shift')
    datum = date.fromisoformat(date_str)
    all_konobari = Zaposleni.objects.filter(tip='K')

    assigned_workers_ids = Smena.objects.filter(datum=datum, broj_smene=int(shift)).values_list('konobar', flat=True)
    assigned_konobari = all_konobari.filter(id__in=assigned_workers_ids)

    available_konobari = all_konobari.exclude(id__in=assigned_workers_ids)

    if request.method == "POST":
        selected_worker_id = request.POST.get('worker')
        if selected_worker_id:
            worker_obj = Zaposleni.objects.get(id=selected_worker_id)
            Smena.objects.create(konobar=worker_obj, datum=datum, broj_smene=int(shift))

        shifts = ["08:00h - 16:00h", "16:00h - 00:00h"]
        today = date.today()
        next_monday = today + timedelta(days=(7 - today.weekday()))
        week_dates = [next_monday + timedelta(days=i) for i in range(7)]
        smene = Smena.objects.filter(datum__in=week_dates)

        firstShiftDict = {day: [] for day in week_dates}
        secondShiftDict = {day: [] for day in week_dates}

        for s in smene:
            name = s.konobar.user.get_full_name()
            if s.broj_smene == 1:
                firstShiftDict[s.datum].append(name)
            elif s.broj_smene == 2:
                secondShiftDict[s.datum].append(name)

        firstShift = [firstShiftDict[day] for day in week_dates]
        secondShift = [secondShiftDict[day] for day in week_dates]
        week_data_first = list(zip(week_dates, firstShift))
        week_data_second = list(zip(week_dates, secondShift))

        return render(request, 'menadzer/napravi_raspored.html', {
            'shifts': shifts,
            'week_dates': week_dates,
            'firstShift': firstShift,
            'secondShift': secondShift,
            'week_data_first': week_data_first,
            'week_data_second': week_data_second
        })

    return render(request, 'menadzer/dodaj_konobara.html', {
        'date': datum,
        'shift': shift,
        'assigned_konobari': assigned_konobari,
        'available_konobari': available_konobari
    })

def stanje_artikala(request):
    """
    **Opis**

    Prikazuje stanje svih :model:`projekat.Artikal` u menadžerskom delu.

    **Context**

    ``artikli``
        Lista svih :model:`projekat.Artikal`.

    **Template**

    :template:`menadzer/stanje.html`

    :param: request: HTML request
    :return: response: HTML response ili redirect ako nije menadžer
    """
    if not request.user.is_authenticated:
        return redirect('prijava')
    if request.user.zap.tip != 'M':
        return redirect_by_role(request.user)
    artikli = Artikal.objects.all()
    return render(request, 'menadzer/stanje.html', {'artikli': artikli})

def statistika(request):
    """
    **Opis**

    Prikazuje formu za izbor :model:`projekat.Artikal`/:model:`projekat.TipArtikla` i vremenskog intervala za generisanje statistike.

    **Context**

    ``artikli``
        Lista svih :model:`projekat.Artikal`.
    ``tipovi``
        Lista svih :model:`projekat.TipArtikla`.

    **Template**

    :template:`menadzer/statistika.html`

    :param: request: HTML request
    :return: response: HTML response ili redirect ako nije menadžer
    """
    if not request.user.is_authenticated:
        return redirect('prijava')
    if request.user.zap.tip != 'M':
        return redirect_by_role(request.user)
    artikli = Artikal.objects.all()
    tipovi = TipArtikla.objects.all()
    return render(request, 'menadzer/statistika.html', {
        'artikli': artikli,
        'tipovi': tipovi
    })

def napravi_statistiku(request):
    """
    **Opis**

    Generiše statistiku prometa :model:`projekat.Artikal` u zadatom vremenskom intervalu, filtriranu po :model:`projekat.TipArtikla` ili po konkretnom :model:`projekat.Artikal`.

    **Context**

        ``statistika``
            Dictionary gde je ključ naziv :model:`projekat.Artikal`, a vrednost ukupna suma prodaje tog :model:`projekat.Artikal`
            u zadatom periodu. Primer: {'Mleko': 1200, 'Hleb': 800}

        ``tip``
            String koji predstavlja naziv :model:`projekat.TipArtikla` ili naziv konkretnog :model:`projekat.Artikal` po kojem je filtrirano.

        ``interval``
            Broj dana za koji je generisana statistika.

        ``ukupno``
            Ukupna suma svih :model:`projekat.Stavka` u filtriranom skupu (suma po svim :model:`projekat.Artikal`).

        ``prikaz_ukupno``
            Boolean koji označava da li treba prikazati red sa ukupnom sumom u šablonu
            (True ako je filtrirano po :model:`projekat.TipArtikla`, False ako je filtrirano po konkretnom :model:`projekat.Artikal`).

    **Template**

    :template:`menadzer/statistika_rezultat.html`

    :param: request: HTML request
    :return: response: HTML response sa statistikom ili redirect na statistika formu
    """
    if not request.user.is_authenticated:
        return redirect('prijava')
    if request.user.zap.tip != 'M':
        return redirect_by_role(request.user)

    if request.method == 'POST':
        izbor = request.POST.get('tip_artikla')
        interval_str = request.POST.get('vremenski_interval', '')

        if not izbor or not interval_str:
            return redirect('statistika')

        interval_dana = int(interval_str)
        pocetak = timezone.now().date() - timedelta(days=interval_dana)
        racuni = Racun.objects.filter(
            status='Z',
            datum_otvaranja__gte=pocetak,
            datum_otvaranja__lte=timezone.now().date()
        )

        stavke = Stavka.objects.filter(racun__in=racuni)
        naziv_filtera = None
        prikaz_ukupno = False

        if izbor.startswith('tip_'):
            tip_id = int(izbor.split('_')[1])
            stavke = stavke.filter(artikal__tip_artikla_id=tip_id)
            naziv_filtera = TipArtikla.objects.get(id=tip_id).naziv
            prikaz_ukupno = True

        elif izbor.startswith('artikal_'):
            artikal_id = int(izbor.split('_')[1])
            stavke = stavke.filter(artikal_id=artikal_id)
            naziv_filtera = Artikal.objects.get(id=artikal_id).naziv
            prikaz_ukupno = False

        statistika = {}
        ukupno = 0
        for s in stavke:
            naziv = s.artikal.naziv
            statistika[naziv] = statistika.get(naziv, 0) + s.cena
            ukupno+=s.cena

        return render(request, 'menadzer/statistika_rezultat.html', {
            'statistika': statistika,
            'tip': naziv_filtera,
            'interval': interval_dana,
            'ukupno': ukupno,
            'prikaz_ukupno': prikaz_ukupno,
        })
    return redirect('statistika')
def qr_kod(request):
    """
    **Opis**

    Generiše QR kod za :model:`projekat.Sto` koji vodi na URL.

    **Context**

    ``stolovi``
        Lista svih :model:`projekat.Sto`.
    ``qr``
        Base64 enkodovan QR kod slike (ako je POST).

    **Template**

    :template:`menadzer/qr_kod.html`

    :param: request: HTML request
    :return: response: HTML response sa formom i generisanim QR kodom
    """
    if not request.user.is_authenticated:
        return redirect('prijava')
    if request.user.zap.tip != 'M':
        return redirect_by_role(request.user)

    if request.method == "POST":
        id = int(request.POST['sto_id'])
        buffer = generate_qr(id)
        qr = base64.b64encode(buffer.getvalue()).decode()
    else:
        qr = None
    return render(request, 'menadzer/qr_kod.html', {'stolovi': Sto.objects.all(), 'qr': qr})

def get_local_ip():
    """
    **Opis**

    Dobija lokalnu IP adresu servera kako bi se mogao generisati URL za QR kod.

    **Return**

    ``ip``
        String lokalne IP adrese servera (npr. '192.168.1.100').

    **Napomena**

    Koristi UDP socket konekciju ka Google DNS (8.8.8.8) da odredi lokalnu adresu, bez slanja podataka.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip

def generate_qr(id):
    """
    **Opis**

    Generiše QR kod za :model:`projekat.Sto` sa zadatim ID-jem, koji vodi na URL ulaza korisnika.

    **Parametri**

    ``id``
        Identifikator :model:`projekat.Sto`.

    **Return**

    ``buffer``
        BytesIO objekat koji sadrži PNG sliku QR koda.

    **Detalji**

    - Dobija lokalnu IP adresu servera preko `get_local_ip`.
    - Kreira URL u formatu ``http://<IP>:8000/projekat/ulaz/<id>/``.
    - QR kod ima crni foreground i beli background, veličina box-a 10, border 4.
    """
    ip = get_local_ip()
    if id == -1:
        url = "https://www.youtube.com/watch?v=Cg_9jp_jli4&list=RDCg_9jp_jli4&start_radio=1"
    else:
        url = f"http://{ip}:8000/projekat/ulaz/{id}/"

    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer