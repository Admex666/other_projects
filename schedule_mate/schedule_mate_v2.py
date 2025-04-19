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

def calculate_break_duration_minutes(difficulty_point):
    if difficulty_point < 1.0:
        return 5
    elif difficulty_point < 2.0:
        return 10
    elif difficulty_point < 3.0:
        return 20
    else:
        return 30

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
    tasks_flex_df['priority_score'] = tasks_flex_df['importance'] * 2 + tasks_flex_df['priority']
    tasks_flex_df = tasks_flex_df.sort_values(by='priority_score', ascending=False).reset_index(drop=True)
    tasks_flex_df[['sessions_so_far', 'time_so_far']] = 0

    scheduled_tasks = []
    remaining_slots = free_slots.copy()
    
    # Init daily task hours (include all task types from rules)
    daily_task_hours = {day: {task_type: 0 for task_type in rules_daylimit['task_type']} for day in free_slots['start'].dt.date.unique()}

    # Add fix tasks to schedule and accumulate daily hours
    for _, fix_task in tasks_fix_df.iterrows():
        start, end = fix_task['start_date'], fix_task['end_date']
        duration = (end - start).total_seconds() / 3600
        day = start.date()
        t_type = fix_task['task_type']
        daily_task_hours[day][t_type] += duration

        scheduled_tasks.append({
            'task': fix_task['task'],
            'task_type': fix_task['task_type'],
            'start_date': start,
            'end_date': end,
            'time(h)': duration,
            'difficulty_points': fix_task['difficulty_points'],
            'priority': fix_task.get('priority'),
            'importance': fix_task.get('importance')
        })

    # Haladás időrendben slot szerint
    for i, slot in remaining_slots.iterrows():
        slot_start = slot['start']
        slot_end = slot['end']
        slot_duration = slot['duration']
        day = slot_start.date()

        # Nézd meg, hogy mi volt az utolsó task előtte
        prior_tasks = [t for t in scheduled_tasks if t['end_date'] <= slot_start]
        if prior_tasks:
            last_task = max(prior_tasks, key=lambda t: t['end_date'])
            last_task_end = last_task['end_date']
            last_task_difficulty = last_task['difficulty_points']
        else:
            last_task_end = None
            last_task_difficulty = 0

        for idx, task in tasks_flex_df.iterrows():
            task_type = task['task_type']
            min_dur = timedelta(hours=task['time(h)_per_session_min'])
            max_dur = timedelta(hours=task['time(h)_per_session_max'])
            time_planned, sesh_max = task[['time(h)_per_week','sessions_per_week_max']]
            sesh_sofar = task['sessions_so_far']
            time_sofar = task['time_so_far']

            if sesh_sofar >= sesh_max or time_sofar >= time_planned * 1.25:
                continue

            if daily_task_hours[day][task_type] + min_dur.total_seconds() / 3600 > rules_daylimit[rules_daylimit['task_type'] == task_type]['limit'].values[0]:
                continue

            if min_dur <= slot_duration:
                actual_dur = min(max_dur, slot_duration)
                scheduled_start = slot_start
                scheduled_end = scheduled_start + actual_dur
                duration_h = actual_dur.total_seconds() / 3600
                difficulty_points = task['difficulty_point_per_hour'] * duration_h

                # Break
                if last_task_end:
                    break_minutes = calculate_break_duration_minutes(last_task_difficulty)
                    break_dur = timedelta(minutes=break_minutes)
                    break_start = scheduled_end
                    break_end = break_start + break_dur
                else:
                    break_minutes = 0
                    break_dur = timedelta()
                    break_start = break_end = scheduled_end

                # Schedule task
                scheduled_tasks.append({
                    'task': task['task'],
                    'task_type': task_type,
                    'start_date': scheduled_start,
                    'end_date': scheduled_end,
                    'time(h)': duration_h,
                    'difficulty_points': difficulty_points,
                    'priority': task['priority'],
                    'importance': task['importance']
                })

                # Schedule break
                scheduled_tasks.append({
                    'task': 'Szünet',
                    'task_type': 'Szünet',
                    'start_date': break_start,
                    'end_date': break_end,
                    'time(h)': break_minutes / 60,
                    'difficulty_points': 0,
                    'priority': None,
                    'importance': None
                })

                # Update task info
                tasks_flex_df.at[idx, 'sessions_so_far'] += 1
                tasks_flex_df.at[idx, 'time_so_far'] += duration_h
                daily_task_hours[day][task_type] += duration_h

                break  # Ezzel a slottal már nem foglalkozunk tovább

    schedule = pd.DataFrame(scheduled_tasks).sort_values(by='start_date').reset_index(drop=True)
    return schedule

schedule_output = schedule_tasks_flex(input_tasks_flex_df, input_tasks_fix_df, free_slots)

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
type_to_color['Szünet'] = '#cccccc'

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

#%% to excel
schedule_output.to_excel(output_file, index=False)
