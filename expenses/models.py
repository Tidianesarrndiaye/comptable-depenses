from calendar import monthrange
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Case, DecimalField, F, Sum, Value, When
from django.db.models.functions import Coalesce


class EntryType(models.TextChoices):
	EXPENSE = 'expense', 'Depense'
	INCOME = 'income', 'Gain'


class EntryCategory(models.TextChoices):
	FOOD = 'food', 'Food'
	CAGNOTE = 'cagnote', 'Cagnote'
	LOAN = 'pret', 'Pret'
	UTILITIES = 'utilities', 'Utilities'
	TRANSPORT = 'transport', 'Transport'
	EXTRAS = 'extras', 'Extras'
	OTHER = 'autre', 'Autre'


class EntryStatus(models.TextChoices):
	DRAFT = 'draft', 'Brouillon'
	SCHEDULED = 'scheduled', 'Planifiee'
	VALIDATED = 'validated', 'Validee'


class Currency(models.TextChoices):
	MAD = 'MAD', 'MAD - Dirham marocain'
	EUR = 'EUR', 'EUR - Euro'
	USD = 'USD', 'USD - Dollar americain'
	XOF = 'XOF', 'XOF - Franc CFA'


class ExpenseSheet(models.Model):
	owner = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='expense_sheets',
	)
	name = models.CharField(max_length=150)
	currency = models.CharField(max_length=3, choices=Currency.choices, default=Currency.MAD)
	starting_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['name']

	def __str__(self):
		return self.name

	@property
	def current_balance(self):
		movements = self.entries.filter(status=EntryStatus.VALIDATED).aggregate(
			total=Coalesce(
				Sum(
					Case(
						When(entry_type=EntryType.INCOME, then=F('amount')),
						When(entry_type=EntryType.EXPENSE, then=F('amount') * Value(-1)),
						default=Value(0),
						output_field=DecimalField(max_digits=12, decimal_places=2),
					)
				),
				Value(Decimal('0.00')),
			)
		)['total']
		return self.starting_balance + movements


class Entry(models.Model):
	sheet = models.ForeignKey(ExpenseSheet, on_delete=models.CASCADE, related_name='entries')
	title = models.CharField(max_length=150)
	entry_type = models.CharField(max_length=10, choices=EntryType.choices)
	category = models.CharField(max_length=20, choices=EntryCategory.choices)
	amount = models.DecimalField(max_digits=12, decimal_places=2)
	entry_date = models.DateField()
	description = models.TextField(blank=True)
	status = models.CharField(max_length=10, choices=EntryStatus.choices, default=EntryStatus.VALIDATED)
	effective_date = models.DateField(null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-entry_date', '-created_at']

	def __str__(self):
		return f'{self.title} ({self.get_entry_type_display()})'

	def clean(self):
		if self.amount <= 0:
			raise ValidationError({'amount': 'Le montant doit etre strictement positif.'})

		if self.status == EntryStatus.SCHEDULED and not self.effective_date:
			raise ValidationError({'effective_date': 'Une entree planifiee doit avoir une date effective.'})

	@property
	def signed_amount(self):
		if self.entry_type == EntryType.EXPENSE:
			return -self.amount
		return self.amount


class RecurringEntryTemplate(models.Model):
	sheet = models.ForeignKey(ExpenseSheet, on_delete=models.CASCADE, related_name='recurring_templates')
	name = models.CharField(max_length=150)
	entry_type = models.CharField(max_length=10, choices=EntryType.choices)
	category = models.CharField(max_length=20, choices=EntryCategory.choices)
	amount = models.DecimalField(max_digits=12, decimal_places=2)
	description = models.TextField(blank=True)
	day_of_month = models.PositiveSmallIntegerField(null=True, blank=True)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['name']

	def __str__(self):
		return self.name

	def clean(self):
		if self.amount <= 0:
			raise ValidationError({'amount': 'Le montant doit etre strictement positif.'})

		if self.day_of_month is not None and not 1 <= self.day_of_month <= 31:
			raise ValidationError({'day_of_month': 'Le jour du mois doit etre compris entre 1 et 31.'})

	def next_due_date(self, reference_date=None):
		reference_date = reference_date or date.today()

		if self.day_of_month is None:
			return reference_date

		year = reference_date.year
		month = reference_date.month
		last_day = monthrange(year, month)[1]
		due_date = date(year, month, min(self.day_of_month, last_day))

		if due_date < reference_date:
			if month == 12:
				year += 1
				month = 1
			else:
				month += 1
			last_day = monthrange(year, month)[1]
			due_date = date(year, month, min(self.day_of_month, last_day))

		return due_date

	def generate_scheduled_entry(self, reference_date=None):
		due_date = self.next_due_date(reference_date=reference_date)
		entry, created = Entry.objects.get_or_create(
			sheet=self.sheet,
			title=self.name,
			status=EntryStatus.SCHEDULED,
			effective_date=due_date,
			defaults={
				'entry_type': self.entry_type,
				'category': self.category,
				'amount': self.amount,
				'entry_date': due_date,
				'description': self.description,
			},
		)
		return entry, created

# Create your models here.
