# Aleksa Sekulic 0021/2022
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import models

# Create your models here.
class Zaposleni(models.Model):
    """
    **Opis**

    Predstavlja jednog zaposlenog povezanog sa jednom insancom User-a.
    Iz user-a se pristupa zaposlenom preko polja zap.
    Vrednosti za tip: 'K' - konobar, 'M' - menadzer, 'A' - admin
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='zap')
    tip = models.CharField(max_length=1)
    def __str__(self):
        return self.user.first_name + ' ' + self.user.last_name
    class Meta:
        db_table = 'zaposleni'


class TipArtikla(models.Model):
    """
    **Opis**

    Predstavlja tip artikla.
    """
    naziv = models.CharField(max_length=45)
    def __str__(self):
        return self.naziv
    class Meta:
        db_table = 'tip_artikla'


class Artikal(models.Model):
    """
    **Opis**

    Predstavlja artikal. Svaki artikal ima svoj :model:`projekat.TipArtikla`.
    """
    tip_artikla = models.ForeignKey(TipArtikla, on_delete=models.CASCADE)
    naziv = models.CharField(max_length=45)
    cena = models.IntegerField()
    velicina_serviranja = models.CharField(max_length=45)
    kolicina_na_stanju = models.IntegerField()
    def __str__(self):
        return self.naziv
    class Meta:
        db_table = 'artikal'


class Dostava(models.Model):
    """
    **Opis**

    Predstavlja jednu dostavu. Svaka dostava ima jedan :model:`projekat.Artikal`.
    Vrednosti za status: 'U TOKU', 'REALIZOVANA', 'OTKAZANA'
    """
    artikal = models.ForeignKey(Artikal, on_delete=models.CASCADE)
    kolicina = models.IntegerField()
    status = models.CharField(max_length=15)
    class Meta:
        db_table = 'dostava'


class Polje(models.Model):
    """
    **Opis**

    Predstavlja polja koja su stolovi i polja koja nisu deo lokala.
    """
    x = models.IntegerField()
    y = models.IntegerField()
    class Meta:
        db_table = 'polje'


class Sto(models.Model):
    """
    **Opis**

    Predstavlja jedan sto. Svaki sto se nalazi na jednom :model:`projekat.Polje`.
    """
    polje = models.ForeignKey(Polje, on_delete=models.CASCADE)
    class Meta:
        db_table = 'sto'


class Rezervacija(models.Model):
    """
    **Opis**

    Predstavlja jednu rezervaciju.
    Vrednosti za status: 'U TOKU', 'REALIZOVANA', 'OTKAZANA'
    """
    sto = models.ForeignKey(Sto, on_delete=models.CASCADE)
    datum_vreme = models.DateTimeField()
    ime = models.CharField(max_length=45)
    status = models.CharField(max_length=15)
    class Meta:
        db_table = 'rezervacija'


class Racun(models.Model):
    """
    **Opis**

    Predstavlja jedan račun. Svaki račun je povezan sa jednim :model:`projekat.Zaposleni` i jedan :model:`projekat.Sto`.
    Vrednosti za status: 'O' - otvoren, 'Z' - zatvoren
    """
    konobar = models.ForeignKey(Zaposleni, on_delete=models.CASCADE)
    sto = models.ForeignKey(Sto, on_delete=models.CASCADE)
    status = models.CharField(max_length=1)
    datum_otvaranja = models.DateField(default=timezone.now)
    class Meta:
        db_table = 'racun'


class Stavka(models.Model):
    """
    **Opis**

    Predstavlja jednu stavku na :model:`projekat.Racun`. Svaka stavka sadrži količinu nekog :model:`projekat.Artikal`.
    """
    racun = models.ForeignKey(Racun, on_delete=models.CASCADE)
    artikal = models.ForeignKey(Artikal, on_delete=models.CASCADE)
    kolicina = models.IntegerField()
    cena = models.IntegerField()
    class Meta:
        db_table = 'stavka'


class Recenzija(models.Model):
    """
    **Opis**

    Predstavlja jednu recenziju. Svaka recenzija se odnosi na jedan :model:`projekat.Racun` i jednog :model:`projekat.Zaposleni`.
    """
    racun = models.ForeignKey(Racun, on_delete=models.CASCADE)
    konobar = models.ForeignKey(Zaposleni, on_delete=models.CASCADE)
    ocena = models.IntegerField()
    class Meta:
        db_table = 'recenzija'


class Smena(models.Model):
    """
    **Opis**

    Predstavlja jednu smenu. Svaka smena se odnosi na jednog :model:`projekat.Zaposleni`.
    """
    konobar = models.ForeignKey(Zaposleni, on_delete=models.CASCADE)
    datum = models.DateField()
    broj_smene = models.IntegerField()
    class Meta:
        db_table = 'smena'