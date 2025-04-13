import pandas as pd
from datetime import datetime, timedelta, time

input_file = "schedule_mate_input.xlsx"
input_tasks_flex_df = pd.read_excel(input_file, sheet_name="Tasks_flex")
input_tasks_fix_df = pd.read_excel(input_file, sheet_name="Tasks_fix")
output_file = 'schedule_mate_output.xlsx'

rules_file = 'schedule_mate_rules.xlsx'
rules_daylimit = pd.read_excel(rules_file, sheet_name='daily_task_hours')

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
    
    daily_task_hours = {day: {task_type: 0 for task_type in rules_daylimit['task_type']} for day in free_slots['start'].dt.date.unique()}
    # add fix task hours as well
    for _, fix_task in tasks_fix_df.iterrows():
        fix_task_start = fix_task['start_date']
        fix_task_end = fix_task['end_date']
        fix_task_duration = (fix_task_end - fix_task_start).total_seconds() / 3600
        
        day = fix_task_start.date()
        task_type = fix_task['task_type']
        
        # Napi órák növelése a fix feladatok idejével
        daily_task_hours[day][task_type] += fix_task_duration
    
    for _, task in tasks_flex_df.iterrows():
        task_duration_min = timedelta(hours=task['time(h)_per_session_min'])
        task_duration_max = timedelta(hours=task['time(h)_per_session_max'])
        time_planned, sesh_max = task[['time(h)_per_week','sessions_per_week_max']]
        sesh_sofar = task['sessions_so_far']
        time_sofar = task['time_so_far']
        
        for i, slot in remaining_slots.iterrows():
            slot_duration = slot['duration']
            
            day = slot['start'].date()
            # Ellenőrizzük, hogy a napi limit nem lett-e túllépve
            task_type = task['task_type']
            daily_hours_used = daily_task_hours[day][task_type]
            if daily_hours_used + task_duration_min.total_seconds() / 3600 > rules_daylimit[rules_daylimit['task_type'] == task_type]['limit'].values[0]:
                continue  # Ha túllépné a limitet, hagyjuk ki ezt a slotot
            
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
                
                # Frissítjük a napi órák számát
                daily_task_hours[day][task_type] += scheduled_duration
                
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
import numpy as np

# Időpontok szétválasztása a napokra
schedule_output['date_only'] = schedule_output['start_date'].dt.date

# Egyedi napok listája
unique_days = schedule_output['date_only'].unique()

# Colormap kiválasztása
cmap = colormaps['rainbow_r']
unique_types = schedule_output['task_type'].unique()
type_to_color = {t: cmap(i / len(unique_types)) for i, t in enumerate(unique_types)}

# Színek hozzárendelése
schedule_output['color'] = schedule_output['task_type'].map(type_to_color)

# Subplots létrehozása, annyi subplot-tal, ahány nap
n_cols = (len(unique_days) + 1) // 2
fig, axes = plt.subplots(nrows=2, ncols=n_cols, figsize=(6*n_cols, 6))

# Ha csak egy nap van, akkor az axes egyetlen objektum lesz, ezt listává kell alakítani.
if len(unique_days) == 1:
    axes = [axes]

# Ha csak egy nap van, akkor az axes egyetlen objektum lesz, ezt listává kell alakítani.
axes = axes.flatten()

# Minden napra külön ábrát rajzolunk
for i, day in enumerate(unique_days):
    ax = axes[i]
    day_data = schedule_output[schedule_output['date_only'] == day]
    
    # Az időpontok órákra átváltása
    day_data['hours_to_start'] = (day_data['start_date'] - day_data['start_date'].min()).dt.total_seconds() / 3600
    
    ax.barh(
        y=day_data['task'],
        width=day_data['time(h)'],
        left=day_data['hours_to_start'],
        color=day_data['color']
    )
    
    ax.set_title(f"Feladatok - {day}")
    ax.set_xlabel("Órák a nap kezdete után")

# Ha maradt üres subplot (pl. ha páratlan napok száma), eltüntetjük
for j in range(i + 1, len(axes)):
    axes[j].axis('off')

plt.tight_layout()  # A subplots közötti helyek optimalizálása
plt.show()
