import pandas as pd
from datetime import datetime, timedelta, time

input_file = "schedule_mate_input.xlsx"
tasks_flex_df = pd.read_excel(input_file, sheet_name="Tasks_flex")
tasks_fix_df = pd.read_excel(input_file, sheet_name="Tasks_fix")

week_start = datetime(2025, 3, 17, 0, 0)
week_end = datetime(2025, 3, 23, 23, 59)

day_start = time(8,30)
day_end = time(22,00)

def compare_day_start(day_start, date_to_check):
    comparison_time = datetime.combine(date_to_check.date(), day_start)
    return True if date_to_check >= comparison_time else False
    
def compare_day_end(day_end, date_to_check):
    comparison_time = datetime.combine(date_to_check.date(), day_end)
    return True if date_to_check <= comparison_time else False

# calculate free slots; df of start and end times
def find_free_slots(tasks_fix_df, week_start, week_end, day_start, day_end):
    free_slots = []
    
    current_day = week_start.date()
    while current_day <= week_end.date():
        day_fix_tasks = tasks_fix_df[
            (tasks_fix_df['start_date'].dt.date == current_day)
            ].sort_values(by='start_date')
        
        day_start_dt = datetime.combine(current_day, day_start)
        day_end_dt = datetime.combine(current_day, day_end)
        
        if day_fix_tasks.empty:
            free_slots.append({'start': day_start_dt, 'end': day_end_dt})
        else:
            prev_end = day_start_dt

            for _, row in day_fix_tasks.iterrows():
                task_start = row['start_date']
                task_end = row['end_date']

                # Ha van szabad idő az előző esemény vége és a következő esemény kezdete között
                if prev_end < task_start:
                    free_slots.append({'start': prev_end, 'end': task_start})

                prev_end = max(prev_end, task_end)  # Ne legyen átfedés

            # Napi végéig fennmaradó szabad idő
            if prev_end < day_end_dt:
                free_slots.append({'start': prev_end, 'end': day_end_dt})

        current_day += timedelta(days=1)

    return pd.DataFrame(free_slots)
    
free_slots = find_free_slots(tasks_fix_df, week_start, week_end, day_start, day_end)
free_slots['duration'] = free_slots.end - free_slots.start
free_slots.duration.sum()

# Add flex tasks to free slots
def redefine_free_slots(free_slots, task_start, task_end):

def add_tasks_flex(tasks_flex_df, tasks_fix_df, free_slots):
    
    schedule = pd.concat([tasks_fix, ]).sort_values(by='start')
    return schedule

add_tasks_flex(tasks_flex_df, tasks_fix_df, free_slots)