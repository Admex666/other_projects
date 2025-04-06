import pandas as pd
from datetime import datetime, timedelta, time

input_file = "schedule_mate_input.xlsx"
input_tasks_flex_df = pd.read_excel(input_file, sheet_name="Tasks_flex")
input_tasks_fix_df = pd.read_excel(input_file, sheet_name="Tasks_fix")
output_file = 'schedule_mate_output.xlsx'

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
    
free_slots = find_free_slots(input_tasks_fix_df, week_start, week_end, day_start, day_end)
free_slots['duration'] = free_slots.end - free_slots.start
free_slots.duration.sum()

# Add flex tasks to free slots
def schedule_tasks_flex(tasks_flex_df, tasks_fix_df, free_slots):
    # Make priorities in flex tasks
    tasks_flex_df['priority_score'] = tasks_flex_df['importance'] * 2 + tasks_flex_df['priority']
    tasks_flex_df = tasks_flex_df.sort_values(by='priority_score', ascending=False).reset_index(drop=True)
    tasks_flex_df[['sessions_so_far', 'time_so_far']] = 0
    
    scheduled_tasks = []
    remaining_slots = free_slots.copy()
    
    for _, task in tasks_flex_df.iterrows():
        task_duration_min = timedelta(hours=task['time(h)_per_session_min'])
        task_duration_max = timedelta(hours=task['time(h)_per_session_max'])
        time_planned, sesh_max = task[['time(h)_per_week','sessions_per_week_max']]
        sesh_sofar = task['sessions_so_far']
        time_sofar = task['time_so_far']
        
        for i, slot in remaining_slots.iterrows():
            slot_duration = slot['duration']
            # check if it fits the slots
            if (task_duration_min <= slot_duration) and (time_sofar < time_planned*1.25):
                # Calculate duration
                duration_to_use = task_duration_max if task_duration_max <= slot_duration else slot_duration
                
                scheduled_start = slot['start']
                scheduled_end = slot['start'] + duration_to_use
                
                scheduled_duration = (scheduled_end - scheduled_start).total_seconds() / 3600
                diff_points = task['difficulty_point_per_hour']*scheduled_duration
                
                scheduled_tasks.append({'task': task['task'],
                                        'task_type': task['task_type'],
                                        'start_date': scheduled_start,
                                        'end_date': scheduled_end,
                                        'time(h)': scheduled_duration,
                                        'difficulty_points': diff_points,
                                        'priority': task['priority'],
                                        'importance': task['importance']})
                
                # Update sessions & time so far
                sesh_sofar += 1
                time_sofar += scheduled_duration
                tasks_flex_df.loc[_,['sessions_so_far', 'time_so_far']] = sesh_sofar, time_sofar 
                
                # Update or delete slot
                remaining_duration = slot_duration - duration_to_use
                if remaining_duration.total_seconds() > 0:
                    remaining_slots.loc[i] = {
                        'start': scheduled_end,
                        'end': slot['end'],
                        'duration': remaining_duration
                    }
                else:
                    remaining_slots.drop(index=i, inplace=True)
    
    schedule = pd.DataFrame(scheduled_tasks)
    schedule_with_fix = pd.concat([schedule, tasks_fix_df]).sort_values(by='start_date').reset_index(drop=True)
    
    return schedule_with_fix

schedule_output = schedule_tasks_flex(input_tasks_flex_df, input_tasks_fix_df, free_slots)

#%% to excel
schedule_output.to_excel(output_file, index=False)

#%%plot
import matplotlib.pyplot as plt
from matplotlib import colormaps

schedule_output['hours_to_start'] = (schedule_output['start_date'] - schedule_output.loc[0, 'start_date']).dt.total_seconds() / 3600

cmap = colormaps['rainbow_r']
unique_types = schedule_output['task_type'].unique()
type_to_color = {t: cmap(i / len(unique_types)) for i, t in enumerate(unique_types)}
colors = schedule_output['task_type'].map(type_to_color)

plt.barh(y=schedule_output['task'], width=schedule_output['time(h)'], 
         left=schedule_output['hours_to_start'], color=colors)
plt.show()