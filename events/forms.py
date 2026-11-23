from django import forms 
from events.models import Event
from core.forms import StyledFormMixin

class EventForm(StyledFormMixin, forms.ModelForm):
    date = forms.DateField(
        label="Event Date",
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    time = forms.TimeField(
        label="Event Time",
        required=False,
        widget=forms.TimeInput(attrs={'type': 'time'})
    )

    class Meta:
        model = Event
        fields = [
            'title','description','event_type','club','date','time','location',
            'image','max_capacity','is_online','notice','website','facebook'
        ]
