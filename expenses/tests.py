from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import Entry, EntryCategory, EntryStatus, EntryType, ExpenseSheet, RecurringEntryTemplate


class HomeViewTests(TestCase):
	def test_home_page_renders_successfully(self):
		response = self.client.get(reverse('expenses:home'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Suivi clair des depenses et des gains.')

	def test_entry_list_page_renders_entries(self):
		sheet = ExpenseSheet.objects.create(name='Budget maison')
		Entry.objects.create(
			sheet=sheet,
			title='Prime',
			entry_type=EntryType.INCOME,
			category=EntryCategory.OTHER,
			amount=Decimal('80.00'),
			entry_date='2026-03-21',
		)

		response = self.client.get(reverse('expenses:entry-list'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Prime')

	def test_entry_list_can_filter_by_status_and_category(self):
		sheet = ExpenseSheet.objects.create(name='Budget maison')
		Entry.objects.create(
			sheet=sheet,
			title='Courses',
			entry_type=EntryType.EXPENSE,
			category=EntryCategory.FOOD,
			amount=Decimal('50.00'),
			entry_date='2026-03-21',
			status=EntryStatus.VALIDATED,
		)
		Entry.objects.create(
			sheet=sheet,
			title='Prime draft',
			entry_type=EntryType.INCOME,
			category=EntryCategory.OTHER,
			amount=Decimal('75.00'),
			entry_date='2026-03-21',
			status=EntryStatus.DRAFT,
		)

		response = self.client.get(reverse('expenses:entry-list'), {'status': EntryStatus.VALIDATED, 'category': EntryCategory.FOOD})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Courses')
		self.assertNotContains(response, 'Prime draft')

	def test_entry_list_displays_current_balance_for_filtered_sheet(self):
		sheet = ExpenseSheet.objects.create(name='Budget principal', starting_balance=Decimal('100.00'))
		Entry.objects.create(
			sheet=sheet,
			title='Salaire',
			entry_type=EntryType.INCOME,
			category=EntryCategory.OTHER,
			amount=Decimal('250.00'),
			entry_date='2026-03-20',
			status=EntryStatus.VALIDATED,
		)
		Entry.objects.create(
			sheet=sheet,
			title='Courses',
			entry_type=EntryType.EXPENSE,
			category=EntryCategory.FOOD,
			amount=Decimal('40.00'),
			entry_date='2026-03-20',
			status=EntryStatus.VALIDATED,
		)

		response = self.client.get(reverse('expenses:entry-list'), {'sheet': sheet.pk})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Solde courant de Budget principal')
		self.assertContains(response, '310,00')

	def test_entry_list_displays_total_current_balance_for_all_sheets(self):
		sheet_one = ExpenseSheet.objects.create(name='Budget A', starting_balance=Decimal('100.00'))
		sheet_two = ExpenseSheet.objects.create(name='Budget B', starting_balance=Decimal('50.00'))

		Entry.objects.create(
			sheet=sheet_one,
			title='Gain A',
			entry_type=EntryType.INCOME,
			category=EntryCategory.OTHER,
			amount=Decimal('40.00'),
			entry_date='2026-03-20',
			status=EntryStatus.VALIDATED,
		)
		Entry.objects.create(
			sheet=sheet_two,
			title='Depense B',
			entry_type=EntryType.EXPENSE,
			category=EntryCategory.FOOD,
			amount=Decimal('10.00'),
			entry_date='2026-03-20',
			status=EntryStatus.VALIDATED,
		)

		response = self.client.get(reverse('expenses:entry-list'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Solde courant total')
		self.assertContains(response, '<strong>180</strong>', html=True)

	def test_home_page_displays_analytics_sections(self):
		sheet = ExpenseSheet.objects.create(name='Budget maison')
		Entry.objects.create(
			sheet=sheet,
			title='Salaire',
			entry_type=EntryType.INCOME,
			category=EntryCategory.OTHER,
			amount=Decimal('1000.00'),
			entry_date='2026-03-10',
			status=EntryStatus.VALIDATED,
		)

		response = self.client.get(reverse('expenses:home'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Vue mensuelle')
		self.assertContains(response, 'Categories dominantes')

	def test_home_page_displays_current_balance_for_sheet(self):
		sheet = ExpenseSheet.objects.create(name='Budget principal', starting_balance=Decimal('100.00'))
		Entry.objects.create(
			sheet=sheet,
			title='Salaire',
			entry_type=EntryType.INCOME,
			category=EntryCategory.OTHER,
			amount=Decimal('250.00'),
			entry_date='2026-03-20',
			status=EntryStatus.VALIDATED,
		)
		Entry.objects.create(
			sheet=sheet,
			title='Courses',
			entry_type=EntryType.EXPENSE,
			category=EntryCategory.FOOD,
			amount=Decimal('40.00'),
			entry_date='2026-03-20',
			status=EntryStatus.VALIDATED,
		)

		response = self.client.get(reverse('expenses:home'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, '310,00')

	def test_home_page_hides_owner_column_for_sheets(self):
		ExpenseSheet.objects.create(name='Budget sans compte', starting_balance=Decimal('50.00'))

		response = self.client.get(reverse('expenses:home'))

		self.assertEqual(response.status_code, 200)
		self.assertNotContains(response, 'Proprietaire')
		self.assertNotContains(response, 'Aucun compte')


class ExpenseSheetBalanceTests(TestCase):
	def test_current_balance_uses_only_validated_entries(self):
		sheet = ExpenseSheet.objects.create(name='Budget principal', starting_balance=Decimal('100.00'))

		Entry.objects.create(
			sheet=sheet,
			title='Salaire',
			entry_type=EntryType.INCOME,
			category=EntryCategory.OTHER,
			amount=Decimal('250.00'),
			entry_date='2026-03-20',
			status=EntryStatus.VALIDATED,
		)
		Entry.objects.create(
			sheet=sheet,
			title='Courses',
			entry_type=EntryType.EXPENSE,
			category=EntryCategory.FOOD,
			amount=Decimal('40.00'),
			entry_date='2026-03-20',
			status=EntryStatus.VALIDATED,
		)
		Entry.objects.create(
			sheet=sheet,
			title='Loyer planifie',
			entry_type=EntryType.EXPENSE,
			category=EntryCategory.UTILITIES,
			amount=Decimal('300.00'),
			entry_date='2026-03-20',
			effective_date='2026-03-28',
			status=EntryStatus.SCHEDULED,
		)

		self.assertEqual(sheet.current_balance, Decimal('310.00'))


class CreationFlowTests(TestCase):
	def test_sheet_can_be_created_from_form(self):
		response = self.client.post(
			reverse('expenses:sheet-create'),
			{
				'name': 'Suivi familial',
				'starting_balance': '150.00',
				'is_active': 'on',
			},
		)

		self.assertEqual(response.status_code, 302)
		self.assertTrue(ExpenseSheet.objects.filter(name='Suivi familial').exists())

	def test_scheduled_entry_can_be_created_from_form(self):
		sheet = ExpenseSheet.objects.create(name='Budget principal')

		response = self.client.post(
			reverse('expenses:entry-create'),
			{
				'sheet': sheet.pk,
				'title': 'Internet',
				'entry_type': EntryType.EXPENSE,
				'category': EntryCategory.UTILITIES,
				'amount': '45.00',
				'entry_date': '2026-03-22',
				'description': 'Abonnement mensuel',
				'status': EntryStatus.SCHEDULED,
				'effective_date': '',
			},
		)

		self.assertEqual(response.status_code, 302)
		entry = Entry.objects.get(title='Internet')
		self.assertEqual(entry.status, EntryStatus.SCHEDULED)
		self.assertEqual(str(entry.effective_date), '2026-03-22')

	def test_entry_can_be_created_without_title(self):
		sheet = ExpenseSheet.objects.create(name='Budget principal')

		response = self.client.post(
			reverse('expenses:entry-create'),
			{
				'sheet': sheet.pk,
				'title': '',
				'entry_type': EntryType.INCOME,
				'category': EntryCategory.OTHER,
				'amount': '120.00',
				'entry_date': '2026-03-23',
				'description': 'Versement',
				'status': EntryStatus.VALIDATED,
				'effective_date': '',
			},
		)

		self.assertEqual(response.status_code, 302)
		entry = Entry.objects.get(amount=Decimal('120.00'))
		self.assertTrue(entry.title)
		self.assertIn('Gain', entry.title)

	def test_recurring_template_generates_scheduled_entry(self):
		sheet = ExpenseSheet.objects.create(name='Budget principal')
		template = RecurringEntryTemplate.objects.create(
			sheet=sheet,
			name='Loyer',
			entry_type=EntryType.EXPENSE,
			category=EntryCategory.UTILITIES,
			amount=Decimal('300.00'),
			day_of_month=25,
		)

		entry, created = template.generate_scheduled_entry(reference_date=__import__('datetime').date(2026, 3, 20))

		self.assertTrue(created)
		self.assertEqual(entry.status, EntryStatus.SCHEDULED)
		self.assertEqual(str(entry.effective_date), '2026-03-25')
