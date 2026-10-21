from django import forms

class LoginForm(forms.Form):
    numero_empleado = forms.CharField(
        label="Número de Empleado / QR",
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Escanea el QR o escribe tu número',
            'autofocus': 'autofocus'
        })
    )
    pin = forms.CharField(
        label="PIN (6 dígitos)",
        max_length=6,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': '••••••',
            'inputmode': 'numeric'
        })
    )