from django.contrib import admin

from .models import Entry, ExpenseSheet, RecurringEntryTemplate


@admin.register(ExpenseSheet)
class ExpenseSheetAdmin(admin.ModelAdmin):
	list_display = ('name', 'owner', 'starting_balance', 'is_active', 'created_at')
	list_filter = ('is_active', 'created_at')
	search_fields = ('name', 'owner__username', 'owner__email')


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
	list_display = ('title', 'sheet', 'entry_type', 'category', 'amount', 'status', 'entry_date')
	list_filter = ('entry_type', 'category', 'status', 'entry_date')
	search_fields = ('title', 'description', 'sheet__name')
	date_hierarchy = 'entry_date'


@admin.register(RecurringEntryTemplate)
class RecurringEntryTemplateAdmin(admin.ModelAdmin):
	list_display = ('name', 'sheet', 'entry_type', 'category', 'amount', 'day_of_month', 'is_active')
	list_filter = ('entry_type', 'category', 'is_active')
	search_fields = ('name', 'description', 'sheet__name')

# Register your models here.
