from django import forms

class BooleanListForm(forms.Form):
    """
    Form with several check ticks.
    """

    def __init__(self,_nameprefix):
        """
        """
        self.nameprefix = _nameprefix
        super(forms.Form, self).__init__()

    def setFields(self, kwds):
        """
        Set the fields in the form
        """
        kwds.sort()
        for k in kwds:
            name = self.nameprefix + k
            self.fields[name] = forms.BooleanField(label=k, required=False)

    def setData(self, dict, useprefix=True):
        """
        Set boolean state according to the dictionary
        """
        for key,val in dict.items():
            if useprefix:
                self.data[self.nameprefix+key] = val
            else:
                self.data[key] = val
        self.is_bound = True

