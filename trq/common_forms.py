from django import forms

class CommonUserForm(forms.Form):
    """ Ancestor of user selection forms """
    summary = forms.BooleanField(
        label="summary",
        initial=False
    )

# vi:ts=4:sw=4:expandtab
