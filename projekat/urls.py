# Aleksa Sekulic 0021/2022


from django.urls import path

from .views.prijavaView import *
from .views.adminView import *
from .views.menadzerView import *
from .views.konobarView import *
from .views.gostView import *

urlpatterns = [
    #prijavaView pogledi

    path('', prijava, name='prijava'),
    path('odjava/', odjava , name='odjava'),
    path('restauracija/', restauracija, name='restauracija'),




    #adminView pogledi

    path('admin/', admin, name='admin'),
    path('admin/zaposleni/', zaposleni, name='zaposleni'),
    path('admin/zaposleni/dodaj/', dodaj_zaposlenog, name='dodaj_zaposlenog'),
    path('admin/artikli/', artikli, name='artikli'),
    path('admin/artikli/dodaj/', dodaj_artikal, name='dodaj_artikal'),
    path('admin/artikli/promeni/', promeni_cenu, name='promeni_cenu'),
    path('admin/tipovi_artikala/', tipovi_artikala, name='tipovi_artikala'),
    path('admin/tipovi_artikala/dodaj/', dodaj_tip_artikla, name='dodaj_tip_artikla'),
    path('admin/raspored_stolova/', raspored_stolova, name='raspored_stolova'),




    #menadzerView pogledi

    path('menadzer/', menadzer, name='menadzer'),
    path('menadzer/dostave/', dostave, name='dostave'),
    path('menadzer/dostave/dodaj/', dodaj_dostavu, name='dodaj_dostavu'),
    path('menadzer/rezervacije/', rezervacije, name='rezervacije'),
    path('menadzer/rezervacije/dodaj/', dodaj_rezervaciju, name='dodaj_rezervaciju'),
    path('menadzer/raspored_po_smenama/', raspored_po_smenama, name='raspored_po_smenama'),
    path('menadzer/raspored_po_smenama/dodaj/', dodaj_raspored_po_smenama, name='dodaj_raspored_po_smenama'),
    path('menadzer/stanje_artikala/', stanje_artikala, name='stanje_artikala'),
    path('menadzer/statistika/', statistika, name='statistika'),
    path('menadzer/qr_kod/', qr_kod, name='qr_kod'),
    path('menadzer/dodaj_konobara/', dodaj_konobara, name='dodaj_konobara'),
    path('menadzer/napravi_statistiku/', napravi_statistiku, name='napravi_statistiku'),



    #konobarView pogledi

    path('konobar/', konobar, name='konobar'),
    path('konobar/smene/', smene, name='smene'),
    path('konobar/stolovi/', stolovi, name='stolovi'),
    path('konobar/racun/<int:id>/', racun, name='racun'),
    path('konobar/stavka/<int:id>/', stavka, name='stavka'),




    #gostView pogledi

    path('gost/', pocetna, name='pocetna'),
    path('gost/karta_pica/', karta_pica, name='karta_pica'),
    path('gost/racun/<int:id>/', racun_gost, name='racun_gost'),
    path('gost/oceni_nas/', oceni_nas, name='oceni_nas'),
    path('ulaz/<int:id>/', ulaz, name='ulaz'),
]