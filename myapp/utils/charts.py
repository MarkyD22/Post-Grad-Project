import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for web apps
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from datetime import datetime, timedelta

def get_graph():
    """Convert matplotlib figure to base64 string for embedding in HTML"""
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight')
    buffer.seek(0)
    image_png = buffer.getvalue()
    graph = base64.b64encode(image_png)
    graph = graph.decode('utf-8')
    buffer.close()
    plt.close()
    return graph

def create_upcoming_tasks_chart(equipment_list):
    """Create a bar chart showing equipment due in next 2 weeks"""
    
    # Count equipment by status
    overdue_count = 0
    due_this_week = 0
    due_next_week = 0
    
    today = datetime.now().date()
    week_1 = today + timedelta(days=7)
    week_2 = today + timedelta(days=14)
    
    for equipment in equipment_list:
        # Check calibration due date
        if equipment.next_calibration_date:
            if equipment.next_calibration_date < today:
                overdue_count += 1
            elif equipment.next_calibration_date <= week_1:
                due_this_week += 1
            elif equipment.next_calibration_date <= week_2:
                due_next_week += 1
        
        # Check maintenance due date
        if equipment.next_maintenance_date:
            if equipment.next_maintenance_date < today:
                overdue_count += 1
            elif equipment.next_maintenance_date <= week_1:
                due_this_week += 1
            elif equipment.next_maintenance_date <= week_2:
                due_next_week += 1
    
    # Create the chart
    categories = ['Overdue', 'Due This Week', 'Due Next Week']
    counts = [overdue_count, due_this_week, due_next_week]
    colors = ['#FF6B6B', '#FFD93D', '#4CAF50']
    
    plt.figure(figsize=(10, 6))
    plt.bar(categories, counts, color=colors)
    plt.title('Maintenance & Calibration Status', fontsize=16, fontweight='bold')
    plt.ylabel('Number of Tasks', fontsize=12)
    plt.xlabel('Status', fontsize=12)
    
    # Add value labels on bars
    for i, v in enumerate(counts):
        plt.text(i, v + 0.5, str(v), ha='center', fontweight='bold')
    
    plt.tight_layout()
    return get_graph()