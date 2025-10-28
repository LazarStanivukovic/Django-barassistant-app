#Sofija Pavlovic 0340/2022

from django import forms

from projekat.models import TipArtikla

TIP_ZAPOSLENOG_CHOICES = [
    ('K', 'Konobar'),
    ('M', 'Menadžer'),
    ('A', 'Administrator'),
]

class ZaposleniForm(forms.Form):
    first_name = forms.CharField(
        label='Ime',
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'style':'padding:8px; font-size:1em; width:200px;'}),
        error_messages={'required': 'Molimo unesite ime.'}
    )
    last_name = forms.CharField(
        label='Prezime',
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'style':'padding:8px; font-size:1em; width:200px;'}),
        error_messages={'required': 'Molimo unesite prezime.'}
    )
    email = forms.EmailField(
        label='Email',
        required=True,
        widget=forms.EmailInput(attrs={'style':'padding:8px; font-size:1em; width:200px;'}),
        error_messages={'required': 'Molimo unesite email.'}
    )
    username = forms.CharField(
        label='Korisničko ime',
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'style':'padding:8px; font-size:1em; width:200px;'}),
        error_messages={'required': 'Molimo unesite korisničko ime.'}
    )
    password = forms.CharField(
        label='Lozinka',
        required=True,
        widget=forms.PasswordInput(attrs={'style':'padding:8px; font-size:1em; width:200px;'}),
        error_messages={'required': 'Molimo unesite lozinku.'}
    )
    tip = forms.ChoiceField(
        label='Tip zaposlenog',
        choices=TIP_ZAPOSLENOG_CHOICES,
        widget=forms.RadioSelect,
        required=True,
        error_messages={'required': 'Molimo izaberite tip zaposlenog.'}
    )

class ArtikalForm(forms.Form):
    naziv = forms.CharField(
        label='Naziv',
        required=True,
        widget=forms.TextInput(attrs={'style':'padding:8px; font-size:1em; width:200px;'}),
        error_messages={'required': 'Molimo unesite naziv artikla.'}
    )

    cena=forms.IntegerField(
        label='Cena',
        required=True,
        min_value=0,
        widget=forms.NumberInput(attrs={'style':'padding:8px; font-size:1em; width:200px;'}),
        error_messages={'required': 'Molimo unesite jedinicnu cenu artikla.'}
    )


    tip = forms.ModelChoiceField(
        label='Tip artikla',
        required=True,
        empty_label=None,
        queryset=TipArtikla.objects.all(),
        widget=forms.Select(attrs={'style': 'padding:8px; font-size:1em; width:200px; margin-top:5px;'}),
        error_messages={'required': 'Molimo izaberite tip artikla.'}
    )