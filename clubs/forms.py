from django import forms
from django.utils import timezone
from clubs.models import Club, ClubRole, ClubMembership
from core.forms import StyledFormMixin

class ClubForm(StyledFormMixin, forms.ModelForm):
    created_at = forms.DateTimeField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    class Meta:
        model = Club
        fields = ['name', 'description', 'image', 'created_at', 'website', 'facebook', 'instagram', 'email']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Enter club name'}),
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe your club'}),
            'image': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        }

    def clean_created_at(self):
        created_at = self.cleaned_data.get('created_at')
        if not created_at:
            return timezone.now()
        return created_at



# class ClubRoleForm(StyledFormMixin, forms.ModelForm):
#     class Meta:
#         model = ClubRole
#         fields = ['club', 'role_name']
#         widgets = {
#             'club': forms.Select(),
#             'role_name': forms.TextInput(attrs={'placeholder': 'e.g. President, Secretary, Member'}),
#         }
class ClubRoleForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ClubRole
        fields = ['role_name']
        widgets = {
            'role_name': forms.TextInput(attrs={
                'class': 'w-full border-gray-300 rounded-lg focus:ring focus:ring-blue-200 px-3 py-2',
                'placeholder': 'e.g. President, Secretary, Treasurer'
            }),
        }
class ClubMembershipForm(StyledFormMixin, forms.ModelForm):
    class Meta:
        model = ClubMembership
        fields = ['user', 'club', 'role']
        widgets = {
            'user': forms.Select(),
            'club': forms.Select(),
            'role': forms.Select(),
        }
