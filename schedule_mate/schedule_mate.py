#%% Segédfüggvények
import pandas as pd
from datetime import datetime, timedelta


def parse_datetime(s):
    s = s.replace(".", "").strip()
    try:
        dt = datetime.strptime(s, "%Y %m %d %H:%M")
    except Exception as e:
        print(f"Hiba a dátum parsing során: {s}", e)
        dt = None
    return dt


def compute_free_slots(fixed_schedule, week_start, week_end):
    free_slots = []
    if not fixed_schedule:
        free_slots.append((week_start, week_end))
        return free_slots

    if fixed_schedule[0]["start"] > week_start:
        free_slots.append((week_start, fixed_schedule[0]["start"]))

    for i in range(len(fixed_schedule) - 1):
        end_current = fixed_schedule[i]["end"]
        start_next = fixed_schedule[i+1]["start"]
        if start_next > end_current:
            free_slots.append((end_current, start_next))

    if fixed_schedule[-1]["end"] < week_end:
        free_slots.append((fixed_schedule[-1]["end"], week_end))

    constrained_slots = []
    for slot in free_slots:
        constrained_slots.extend(constrain_slot_to_daily_bounds(slot[0], slot[1]))
    return constrained_slots


def constrain_slot_to_daily_bounds(slot_start, slot_end):
    available_slots = []
    current_day = slot_start.date()
    end_day = slot_end.date()
    while current_day <= end_day:
        day_start = datetime.combine(current_day, datetime.min.time()) + timedelta(hours=8, minutes=30)
        day_end = datetime.combine(current_day, datetime.min.time()) + timedelta(hours=23, minutes=0)
        segment_start = max(slot_start, day_start)
        segment_end = min(slot_end, day_end)
        if segment_start < segment_end:
            available_slots.append((segment_start, segment_end))
        current_day += timedelta(days=1)
    return available_slots


def determine_sessions(total_time, min_sessions, max_sessions, min_session_duration, max_session_duration):
    for sessions in range(int(min_sessions), int(max_sessions) + 1):
        session_duration = total_time / sessions
        if min_session_duration <= session_duration <= max_session_duration:
            return sessions, session_duration
    sessions = int(min_sessions)
    session_duration = max(min_session_duration, min(total_time / sessions, max_session_duration))
    return sessions, session_duration


def find_last_session_ending_at(candidate_start, scheduled_list):
    for sess in scheduled_list:
        if sess["end"] == candidate_start:
            return sess
    return None


def check_new_session_constraints(new_session, scheduled_sessions):
    """
    Ellenőrzi, hogy az új session beillesztése után a rendezett ütemezésben:
      - Két egymást követő feladat ne legyen azonos névvel (task).
      - Maximum két egymás utáni azonos típusú (task_type) feladat legyen.
    """
    temp = scheduled_sessions.copy()
    temp.append(new_session)
    temp.sort(key=lambda x: x["start"])
    index = temp.index(new_session)
    
    # Ellenőrizzük az előző feladat nevét
    if index > 0 and temp[index - 1]["task"] == new_session["task"]:
        return False
    
    # Ellenőrizzük, hogy az előző kettő feladat típusa ugyanaz-e, mint az újé
    if index > 1 and temp[index - 1]["task_type"] == new_session["task_type"] \
            and temp[index - 2]["task_type"] == new_session["task_type"]:
        return False
    
    return True


def schedule_flexible_tasks(tasks_flex_df, free_slots, fixed_schedule):
    flex_schedule = []
    all_scheduled = fixed_schedule.copy()

    for idx, row in tasks_flex_df.iterrows():
        task_name = row["task"]
        task_type = row["task_type"]
        total_time = float(row["time(h)_per_week"])
        min_sessions = float(row["sessions_per_week_min"])
        max_sessions = float(row["sessions_per_week_max"])
        min_session_duration = float(row["time(h)_per_session_min"])
        max_session_duration = float(row["time(h)_per_session_max"])

        sessions, session_duration = determine_sessions(total_time, min_sessions, max_sessions, min_session_duration, max_session_duration)

        for s in range(int(sessions)):
            slot_found = False
            for i in range(len(free_slots)):
                slot_start, slot_end = free_slots[i]
                slot_length = (slot_end - slot_start).total_seconds() / 3600.0
                if slot_length >= session_duration:
                    candidate_start = slot_start
                    prev_session = find_last_session_ending_at(candidate_start, all_scheduled)
                    # Ha az előző session ugyanaz a feladat, toljunk el candidate_start-ot legalább 1/4 session idővel
                    if prev_session is not None and prev_session["task"] == task_name:
                        candidate_start += timedelta(hours=session_duration / 4)
                    candidate_end = candidate_start + timedelta(hours=session_duration)
                    # A candidate eltolása addig, amíg belefér a slotba és a feltételek teljesülnek
                    candidate_valid = False
                    while candidate_end <= slot_end:
                        new_session = {
                            "task": task_name,
                            "task_type": task_type,
                            "start": candidate_start,
                            "end": candidate_end,
                            "duration": session_duration,
                            "difficulty_points": float(row["difficulty_point_per_hour"]) * session_duration,
                            "priority": row["priority"],
                            "importance": row["importance"]
                        }
                        if check_new_session_constraints(new_session, all_scheduled):
                            candidate_valid = True
                            break
                        candidate_start += timedelta(minutes=5)
                        candidate_end = candidate_start + timedelta(hours=session_duration)
                    if candidate_valid:
                        flex_schedule.append(new_session)
                        all_scheduled.append(new_session)
                        # Frissítjük a free slotot: levágjuk a felhasznált részt
                        if candidate_end < slot_end:
                            free_slots[i] = (candidate_end, slot_end)
                        else:
                            free_slots.pop(i)
                        slot_found = True
                        break
            if not slot_found:
                print(f"Figyelmeztetés: Nem sikerült ütemezni a(z) '{task_name}' feladat {s+1}. session-jét!")
    return flex_schedule

#%% Fő kód
input_file = "schedule_mate_input.xlsx"
tasks_flex_df = pd.read_excel(input_file, sheet_name="Tasks_flex")
tasks_fix_df = pd.read_excel(input_file, sheet_name="Tasks_fix")

week_start = datetime(2025, 3, 17, 0, 0)
week_end = datetime(2025, 3, 23, 23, 59)

if tasks_fix_df["start_date"].dtype == '<M8[ns]':
    tasks_fix_df["start_datetime"] = tasks_fix_df["start_date"]
    tasks_fix_df["end_datetime"] = tasks_fix_df["end_date"]
else:
    tasks_fix_df["start_datetime"] = tasks_fix_df["start_date"].apply(parse_datetime)
    tasks_fix_df["end_datetime"] = tasks_fix_df["end_date"].apply(parse_datetime)

fixed_schedule = [{
    "task": row["task"],
    "task_type": row["task_type"],
    "start": row["start_datetime"],
    "end": row["end_datetime"],
    "duration": float(row["time(h)"]),
    "difficulty_points": float(row["difficulty_points"])
} for _, row in tasks_fix_df.iterrows()]

fixed_schedule.sort(key=lambda x: x["start"])
free_slots = compute_free_slots(fixed_schedule, week_start, week_end)

flex_schedule = schedule_flexible_tasks(tasks_flex_df, free_slots, fixed_schedule)
full_schedule = fixed_schedule + flex_schedule
full_schedule.sort(key=lambda x: x["start"])

output_schedule = pd.DataFrame(full_schedule)
output_schedule["start"] = output_schedule["start"].dt.strftime("%Y-%m-%d %H:%M")
output_schedule["end"] = output_schedule["end"].dt.strftime("%Y-%m-%d %H:%M")

output_file = "schedule_mate_output.xlsx"
with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    output_schedule.to_excel(writer, sheet_name="Schedule", index=False)

print(f"Ütemezés elkészült. Az eredmény a {output_file} fájlban található.")
