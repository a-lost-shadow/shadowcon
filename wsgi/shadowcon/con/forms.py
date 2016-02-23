from django.forms import CharField
from registration.forms import RegistrationForm as BaseRegistrationForm, get_user_model


class RegistrationForm(BaseRegistrationForm):
    first_name = CharField(max_length=30, required=False)
    last_name = CharField(max_length=30, required=False)

    class Meta(BaseRegistrationForm.Meta):
        fields = [
            get_user_model().USERNAME_FIELD,
            'first_name',
            'last_name',
            'email',
            'password1',
            'password2'
        ]
