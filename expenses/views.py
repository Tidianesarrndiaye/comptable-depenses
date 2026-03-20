import csv
from decimal import Decimal

from django.contrib import messages
from django.db.models import Case, Count, DecimalField, F, Sum, Value, When
from django.db.models.functions import Coalesce, TruncMonth
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from openpyxl import Workbook

from .forms import EntryForm, ExpenseSheetForm, RecurringEntryTemplateForm
from .models import Currency, Entry, EntryCategory, EntryStatus, EntryType, ExpenseSheet, RecurringEntryTemplate


def get_currency_hint_for_active_sheets():
	active_currencies = list(
		ExpenseSheet.objects.filter(is_active=True).values_list('currency', flat=True).distinct()
	)
	if len(active_currencies) == 1:
		return active_currencies[0]
	if len(active_currencies) > 1:
		return 'MULTI'
	return Currency.MAD


def build_financial_summary(entries):
	return entries.aggregate(
		income_total=Coalesce(
			Sum(
				Case(
					When(entry_type=EntryType.INCOME, then=F('amount')),
					default=Value(Decimal('0.00')),
					output_field=DecimalField(max_digits=12, decimal_places=2),
				)
			),
			Value(Decimal('0.00')),
		),
		expense_total=Coalesce(
			Sum(
				Case(
					When(entry_type=EntryType.EXPENSE, then=F('amount')),
					default=Value(Decimal('0.00')),
					output_field=DecimalField(max_digits=12, decimal_places=2),
				)
			),
			Value(Decimal('0.00')),
		),
		net_total=Coalesce(
			Sum(
				Case(
					When(entry_type=EntryType.INCOME, then=F('amount')),
					When(entry_type=EntryType.EXPENSE, then=F('amount') * Value(-1)),
					default=Value(Decimal('0.00')),
					output_field=DecimalField(max_digits=12, decimal_places=2),
				)
			),
			Value(Decimal('0.00')),
		),
	)


def get_filtered_entries(request):
	entries = Entry.objects.select_related('sheet').all()
	selected_sheet = request.GET.get('sheet', '').strip()
	selected_type = request.GET.get('entry_type', '').strip()
	selected_category = request.GET.get('category', '').strip()
	selected_status = request.GET.get('status', '').strip()
	date_from = request.GET.get('date_from', '').strip()
	date_to = request.GET.get('date_to', '').strip()

	if selected_sheet:
		entries = entries.filter(sheet_id=selected_sheet)
	if selected_type:
		entries = entries.filter(entry_type=selected_type)
	if selected_category:
		entries = entries.filter(category=selected_category)
	if selected_status:
		entries = entries.filter(status=selected_status)
	if date_from:
		entries = entries.filter(entry_date__gte=date_from)
	if date_to:
		entries = entries.filter(entry_date__lte=date_to)

	return entries, {
		'selected_sheet': selected_sheet,
		'selected_type': selected_type,
		'selected_category': selected_category,
		'selected_status': selected_status,
		'date_from': date_from,
		'date_to': date_to,
	}


def home(request):
	validated_entries = Entry.objects.filter(status=EntryStatus.VALIDATED)
	financial_summary = build_financial_summary(validated_entries)
	dashboard_currency_hint = get_currency_hint_for_active_sheets()
	monthly_summary = list(
		validated_entries.annotate(month=TruncMonth('entry_date'))
		.values('month')
		.annotate(
			income_total=Coalesce(
				Sum(
					Case(
						When(entry_type=EntryType.INCOME, then=F('amount')),
						default=Value(Decimal('0.00')),
						output_field=DecimalField(max_digits=12, decimal_places=2),
					)
				),
				Value(Decimal('0.00')),
			),
			expense_total=Coalesce(
				Sum(
					Case(
						When(entry_type=EntryType.EXPENSE, then=F('amount')),
						default=Value(Decimal('0.00')),
						output_field=DecimalField(max_digits=12, decimal_places=2),
					)
				),
				Value(Decimal('0.00')),
			),
		)
		.order_by('-month')[:6]
	)
	category_breakdown = list(
		validated_entries.values('category')
		.annotate(total=Coalesce(Sum('amount'), Value(Decimal('0.00'))), movement_count=Count('id'))
		.order_by('-total', 'category')[:7]
	)
	for row in category_breakdown:
		row['label'] = dict(EntryCategory.choices).get(row['category'], row['category'])

	context = {
		'sheet_count': ExpenseSheet.objects.count(),
		'entry_count': Entry.objects.count(),
		'validated_entry_count': Entry.objects.filter(status=EntryStatus.VALIDATED).count(),
		'scheduled_entry_count': Entry.objects.filter(status=EntryStatus.SCHEDULED).count(),
		'template_count': RecurringEntryTemplate.objects.count(),
		'financial_summary': financial_summary,
		'dashboard_currency_hint': dashboard_currency_hint,
		'monthly_summary': monthly_summary,
		'category_breakdown': category_breakdown,
		'recent_entries': Entry.objects.select_related('sheet')[:5],
		'latest_sheets': ExpenseSheet.objects.annotate(entry_total=Count('entries')).order_by('-created_at')[:5],
	}
	return render(request, 'expenses/home.html', context)


def expense_sheet_create(request):
	form = ExpenseSheetForm(request.POST or None)

	if request.method == 'POST' and form.is_valid():
		form.save()
		messages.success(request, 'La feuille de depenses a ete creee.')
		return redirect('expenses:home')

	return render(request, 'expenses/expense_sheet_form.html', {'form': form})


def expense_sheet_update(request, pk):
	sheet = get_object_or_404(ExpenseSheet, pk=pk)
	form = ExpenseSheetForm(request.POST or None, instance=sheet)

	if request.method == 'POST' and form.is_valid():
		form.save()
		messages.success(request, 'La feuille de depenses a ete mise a jour.')
		return redirect('expenses:home')

	return render(request, 'expenses/expense_sheet_form.html', {'form': form, 'sheet': sheet})


def entry_create(request):
	form = EntryForm(request.POST or None)

	if request.method == 'POST' and form.is_valid():
		entry = form.save()
		if entry.status == EntryStatus.SCHEDULED and entry.effective_date == entry.entry_date:
			messages.success(request, 'L entree planifiee a ete creee avec sa date effective.')
		else:
			messages.success(request, 'L entree a ete creee.')
		return redirect('expenses:entry-list')

	return render(request, 'expenses/entry_form.html', {'form': form})


def entry_list(request):
	entries, filters = get_filtered_entries(request)
	selected_sheet_obj = None
	current_balance_total = Decimal('0.00')
	global_currency_hint = get_currency_hint_for_active_sheets()
	if filters['selected_sheet']:
		selected_sheet_obj = ExpenseSheet.objects.filter(pk=filters['selected_sheet']).first()
		if selected_sheet_obj:
			current_balance_total = selected_sheet_obj.current_balance
	else:
		total_starting = ExpenseSheet.objects.filter(is_active=True).aggregate(
			total=Coalesce(Sum('starting_balance'), Value(Decimal('0.00')))
		)['total']
		total_movements = Entry.objects.filter(
			sheet__is_active=True,
			status=EntryStatus.VALIDATED,
		).aggregate(
			total=Coalesce(
				Sum(
					Case(
						When(entry_type=EntryType.INCOME, then=F('amount')),
						When(entry_type=EntryType.EXPENSE, then=F('amount') * Value(-1)),
						default=Value(Decimal('0.00')),
						output_field=DecimalField(max_digits=12, decimal_places=2),
					)
				),
				Value(Decimal('0.00')),
			)
		)['total']
		current_balance_total = total_starting + total_movements

	financial_summary = build_financial_summary(entries.filter(status=EntryStatus.VALIDATED))
	context = {
		'entries': entries,
		'validated_total': entries.filter(status=EntryStatus.VALIDATED).count(),
		'scheduled_total': entries.filter(status=EntryStatus.SCHEDULED).count(),
		'draft_total': entries.filter(status=EntryStatus.DRAFT).count(),
		'income_total': financial_summary['income_total'],
		'expense_total': financial_summary['expense_total'],
		'net_total': financial_summary['net_total'],
		'sheets': ExpenseSheet.objects.filter(is_active=True).order_by('name'),
		'entry_type_choices': EntryType.choices,
		'category_choices': EntryCategory.choices,
		'status_choices': EntryStatus.choices,
		'active_query': request.GET.urlencode(),
		'selected_sheet_obj': selected_sheet_obj,
		'current_balance_total': current_balance_total,
		'global_currency_hint': global_currency_hint,
		'currency_labels': dict(Currency.choices),
	}
	context.update(filters)
	return render(request, 'expenses/entry_list.html', context)


def export_entries_csv(request):
	entries, _ = get_filtered_entries(request)
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="mouvements.csv"'
	response.write('\ufeff')

	writer = csv.writer(response)
	writer.writerow(['Date', 'Titre', 'Feuille', 'Type', 'Categorie', 'Montant', 'Statut', 'Date effective'])
	for entry in entries:
		writer.writerow(
			[
				entry.entry_date,
				entry.title,
				entry.sheet.name,
				entry.get_entry_type_display(),
				entry.get_category_display(),
				entry.amount,
				entry.get_status_display(),
				entry.effective_date or '',
			]
		)

	return response


def export_entries_excel(request):
	entries, _ = get_filtered_entries(request)
	workbook = Workbook()
	worksheet = workbook.active
	worksheet.title = 'Mouvements'
	worksheet.append(['Date', 'Titre', 'Feuille', 'Type', 'Categorie', 'Montant', 'Statut', 'Date effective'])

	for entry in entries:
		worksheet.append(
			[
				entry.entry_date.isoformat(),
				entry.title,
				entry.sheet.name,
				entry.get_entry_type_display(),
				entry.get_category_display(),
				float(entry.amount),
				entry.get_status_display(),
				entry.effective_date.isoformat() if entry.effective_date else '',
			]
		)

	response = HttpResponse(
		content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
	)
	response['Content-Disposition'] = 'attachment; filename="mouvements.xlsx"'
	workbook.save(response)
	return response


def recurring_template_create(request):
	form = RecurringEntryTemplateForm(request.POST or None)
	templates = RecurringEntryTemplate.objects.select_related('sheet').filter(is_active=True)

	if request.method == 'POST' and form.is_valid():
		form.save()
		messages.success(request, 'Le modele recurrent a ete enregistre.')
		return redirect('expenses:template-create')

	return render(
		request,
		'expenses/recurring_template_form.html',
		{
			'form': form,
			'templates': templates,
		},
	)


def generate_scheduled_entries(request):
	if request.method == 'POST':
		created_count = 0
		for template in RecurringEntryTemplate.objects.filter(is_active=True).select_related('sheet'):
			_, created = template.generate_scheduled_entry()
			created_count += int(created)

		messages.success(request, f'{created_count} entree(s) planifiee(s) ont ete generee(s).')

	return redirect('expenses:entry-list')


@require_POST
def expense_sheet_delete(request, pk):
	sheet = get_object_or_404(ExpenseSheet, pk=pk)
	sheet_name = sheet.name
	sheet.delete()
	messages.success(request, f'La feuille "{sheet_name}" a ete supprimee.')
	return redirect('expenses:home')


@require_POST
def entry_delete(request, pk):
	entry = get_object_or_404(Entry, pk=pk)
	entry_title = entry.title
	entry.delete()
	messages.success(request, f'L entree "{entry_title}" a ete supprimee.')
	return redirect('expenses:entry-list')

# Create your views here.
