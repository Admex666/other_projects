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
    free_slots = pd.DataFrame()
    if not tasks_fix_df:
        free_slots.loc[len(free_slots), ['start', 'end']] = [week_start, week_end]
        return free_slots
    
    if tasks_fix_df.loc[0, 'start_date'] > week_start:
        slot = [week_start, tasks_fix_df.loc[0, 'start_date']]
        free_slots.loc[len(free_slots), ['start', 'end']] = slot
        
    for i in range(1, len(tasks_fix_df)-1):
        print(tasks_fix_df.loc[i,'start_date'])
    
    return free_slots
    
