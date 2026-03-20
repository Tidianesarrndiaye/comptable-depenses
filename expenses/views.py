from decimal import Decimal

from django.contrib import messages
from django.db.models import Case, Count, DecimalField, F, Sum, Value, When
from django.db.models.functions import Coalesce, TruncMonth
from django.shortcuts import redirect, render

from .forms import EntryForm, ExpenseSheetForm, RecurringEntryTemplateForm
from .models import Entry, EntryCategory, EntryStatus, EntryType, ExpenseSheet, RecurringEntryTemplate


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


def home(request):
	validated_entries = Entry.objects.filter(status=EntryStatus.VALIDATED)
	financial_summary = build_financial_summary(validated_entries)
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
		'selected_sheet': selected_sheet,
		'selected_type': selected_type,
		'selected_category': selected_category,
		'selected_status': selected_status,
		'date_from': date_from,
		'date_to': date_to,
	}
	return render(request, 'expenses/entry_list.html', context)


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

# Create your views here.
