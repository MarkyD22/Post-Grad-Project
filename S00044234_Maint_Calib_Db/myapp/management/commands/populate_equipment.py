from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import random
from myapp.models import Equipment

class Command(BaseCommand):
    help = 'Populate database with sample equipment data'

    def handle(self, *args, **options):
        # Sample data based on your project requirements
        sample_equipment = [
            {
                'Machine_ID': 'CNC001',
                'Machine_Name': 'CNC Machining Center #1',
                'Machine_Type': 'cnc_machine',
                'Machine_Location': 'Production Floor A',
                'manufacturer': 'Haas Automation',
                'model_number': 'VF-2SS'
            },
            {
                'Machine_ID': 'PRESS004',
                'Machine_Name': 'Hydraulic Press #4',
                'Machine_Type': 'press',
                'Machine_Location': 'Production Floor B',
                'manufacturer': 'Greenerd',
                'model_number': 'H-Frame 100T'
            },
            {
                'Machine_ID': 'SCALE009',
                'Machine_Name': 'Precision Scale #9',
                'Machine_Type': 'scale',
                'Machine_Location': 'Quality Lab',
                'manufacturer': 'Mettler Toledo',
                'model_number': 'XS6002S'
            },
            {
                'Machine_ID': 'CONV002',
                'Machine_Name': 'Conveyor System #2',
                'Machine_Type': 'conveyor',
                'Machine_Location': 'Assembly Line 1',
                'manufacturer': 'Dorner',
                'model_number': '2200 Series'
            },
            {
                'Machine_ID': 'TORQUE012',
                'Machine_Name': 'Digital Torque Wrench #12',
                'Machine_Type': 'torque_wrench',
                'Machine_Location': 'Assembly Station 3',
                'manufacturer': 'Snap-on',
                'model_number': 'ATECH3FR250'
            },
        ]
        
        today = timezone.now().date()
        
        for item in sample_equipment:
            # Random dates for last maintenance and calibration
            last_maintenance = today - timedelta(days=random.randint(1, 180))
            last_calibration = today - timedelta(days=random.randint(1, 300))
            
            equipment, created = Equipment.objects.get_or_create(
                Machine_ID=item['Machine_ID'],
                defaults={
                    **item,
                    'Last_Maintenance_Date': last_maintenance,
                    'Last_Calibration_Date': last_calibration,
                    'status': 'active'
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created equipment: {equipment.Machine_ID}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Equipment already exists: {equipment.Machine_ID}')
                )
        
        self.stdout.write(
            self.style.SUCCESS('Successfully populated equipment data!')
        )
        