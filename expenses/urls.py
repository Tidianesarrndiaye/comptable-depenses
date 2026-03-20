from django.urls import path

from .views import (
    entry_delete,
    entry_create,
    entry_list,
    expense_sheet_delete,
    expense_sheet_create,
    expense_sheet_update,
    export_entries_csv,
    export_entries_excel,
    generate_scheduled_entries,
    home,
    recurring_template_create,
)

app_name = 'expenses'

urlpatterns = [
    path('', home, name='home'),
    path('feuilles/nouvelle/', expense_sheet_create, name='sheet-create'),
    path('feuilles/<int:pk>/modifier/', expense_sheet_update, name='sheet-update'),
    path('feuilles/<int:pk>/supprimer/', expense_sheet_delete, name='sheet-delete'),
    path('entrees/', entry_list, name='entry-list'),
    path('entrees/nouvelle/', entry_create, name='entry-create'),
    path('entrees/<int:pk>/supprimer/', entry_delete, name='entry-delete'),
    path('entrees/export/csv/', export_entries_csv, name='entry-export-csv'),
    path('entrees/export/excel/', export_entries_excel, name='entry-export-excel'),
    path('modeles-recurrents/', recurring_template_create, name='template-create'),
    path('modeles-recurrents/generer/', generate_scheduled_entries, name='generate-scheduled'),
]