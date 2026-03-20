from django.db import migrations, models


class Migration(migrations.Migration):

	dependencies = [
		('expenses', '0001_initial'),
	]

	operations = [
		migrations.AddField(
			model_name='expensesheet',
			name='currency',
			field=models.CharField(
				choices=[
					('MAD', 'MAD - Dirham marocain'),
					('EUR', 'EUR - Euro'),
					('USD', 'USD - Dollar americain'),
					('XOF', 'XOF - Franc CFA'),
				],
				default='MAD',
				max_length=3,
			),
		),
	]
