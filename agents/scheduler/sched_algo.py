# scheduler/algorithm.py

def get_eligible_courses(student, course_offerings, prerequisites, degree_plan):
    taken = set(student.get("courses_taken", []))
    year = student.get("year", "year_1")
    quarter = student.get("current_quarter", "Fall")

    eligible = []

    if year in degree_plan:
        year_plan = degree_plan[year]
        for q, courses in year_plan.items():
            for course in courses:
                if course in taken or course not in course_offerings:
                    continue
                prereqs = prerequisites.get(course, [])
                if all(p in taken for p in prereqs):
                    eligible.append({
                        "course": course,
                        "quarter": q,
                        "year": year,
                        "prerequisites": prereqs
                    })

    return {
        "eligible_courses": eligible,
        "student_history": list(taken),
        "current_year": year,
        "current_quarter": quarter
    }


def parse_time(t):
    hours, minutes = map(int, t.split(":"))
    return hours * 60 + minutes


def times_overlap(start1, end1, start2, end2):
    return not (end1 <= start2 or end2 <= start1)


def days_overlap(days1, days2):
    return any(d in days2 for d in days1)

