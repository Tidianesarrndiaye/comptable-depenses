from datetime import date

from django import forms

from .models import Entry, EntryStatus, ExpenseSheet, RecurringEntryTemplate


class ExpenseSheetForm(forms.ModelForm):
	class Meta:
		model = ExpenseSheet
		fields = ['name', 'starting_balance', 'is_active']
		labels = {
			'name': 'Nom de la feuille',
			'starting_balance': 'Solde initial',
			'is_active': 'Feuille active',
		}


class EntryForm(forms.ModelForm):
	class Meta:
		model = Entry
		fields = [
			'sheet',
			'title',
			'entry_type',
			'category',
			'amount',
			'entry_date',
			'description',
			'status',
			'effective_date',
		]
		labels = {
			'sheet': 'Feuille de depenses',
			'title': 'Titre',
			'entry_type': 'Type',
			'category': 'Categorie',
			'amount': 'Montant',
			'entry_date': 'Date de saisie',
			'description': 'Description',
			'status': 'Statut',
			'effective_date': 'Date effective',
		}
		widgets = {
			'entry_date': forms.DateInput(attrs={'type': 'date'}),
			'effective_date': forms.DateInput(attrs={'type': 'date'}),
		}

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['entry_date'].initial = date.today
		self.fields['status'].initial = EntryStatus.VALIDATED
		self.fields['title'].required = False

	def clean(self):
		cleaned_data = super().clean()
		title = (cleaned_data.get('title') or '').strip()
		entry_type = cleaned_data.get('entry_type')
		entry_date = cleaned_data.get('entry_date')
		status = cleaned_data.get('status')
		effective_date = cleaned_data.get('effective_date')

		if not title:
			type_label = dict(Entry._meta.get_field('entry_type').choices).get(entry_type, 'Mouvement')
			date_label = entry_date.isoformat() if entry_date else date.today().isoformat()
			cleaned_data['title'] = f'{type_label} du {date_label}'

		if status == EntryStatus.SCHEDULED and not effective_date:
			cleaned_data['effective_date'] = entry_date

		return cleaned_data


class RecurringEntryTemplateForm(forms.ModelForm):
	class Meta:
		model = RecurringEntryTemplate
		fields = [
			'sheet',
			'name',
			'entry_type',
			'category',
			'amount',
			'description',
			'day_of_month',
			'is_active',
		]
		labels = {
			'sheet': 'Feuille de depenses',
			'name': 'Nom du modele',
			'entry_type': 'Type',
			'category': 'Categorie',
			'amount': 'Montant',
			'description': 'Description',
			'day_of_month': 'Jour du mois',
			'is_active': 'Modele actif',
		}