from django.urls import path

from .views import entry_create, entry_list, expense_sheet_create, generate_scheduled_entries, home, recurring_template_create

app_name = 'expenses'

urlpatterns = [
    path('', home, name='home'),
    path('feuilles/nouvelle/', expense_sheet_create, name='sheet-create'),
    path('entrees/', entry_list, name='entry-list'),
    path('entrees/nouvelle/', entry_create, name='entry-create'),
    path('modeles-recurrents/', recurring_template_create, name='template-create'),
    path('modeles-recurrents/generer/', generate_scheduled_entries, name='generate-scheduled'),
]