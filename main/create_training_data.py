import random
from datetime import timedelta
from django.utils import timezone
from main.models import TrainingCourse

# ============================================================================
# CONSTANTS
# ============================================================================
COURSE_TITLES = {
    'Tech': ["Python Programming Bootcamp", "Web Development Fundamentals", "Data Science Masterclass", "Cloud Computing with AWS", "Cybersecurity Essentials", "Machine Learning A-Z", "Full Stack Development", "Mobile App Development with Flutter", "DevOps Engineering", "Blockchain Fundamentals", "UI/UX Design Principles", "Database Administration", "Network Security Certification", "Artificial Intelligence Basics", "React.js Complete Guide", "JavaScript Advanced Concepts", "Python for Data Analysis", "Docker and Kubernetes", "IT Project Management", "Software Testing Automation"],
    'Business': ["Business Management Certificate", "Digital Marketing Strategy", "Financial Accounting Basics", "Project Management Professional", "Entrepreneurship Essentials", "Leadership Skills Workshop", "Sales Techniques Masterclass", "Business Analytics with Excel", "Supply Chain Management", "Human Resources Fundamentals", "Corporate Communication", "Strategic Planning", "Investment Analysis", "Negotiation Skills Training", "Business Law Basics", "Customer Relationship Management", "E-commerce Business Setup", "Public Speaking Mastery", "Time Management Skills", "Conflict Resolution Workshop"],
    'Art': ["Graphic Design Fundamentals", "Digital Photography Course", "Video Editing Masterclass", "Adobe Photoshop Workshop", "Illustration Techniques", "Typography Basics", "Animation Principles", "3D Modeling with Blender", "Color Theory Workshop", "Portrait Drawing Course", "Creative Writing Workshop", "Film Production Basics", "Music Production Fundamentals", "Interior Design Principles", "Fashion Design Basics", "Art History Overview", "Calligraphy Workshop", "Pottery and Ceramics", "Digital Painting Course", "Architecture Fundamentals"],
    'Health': ["Nutrition and Wellness Coach", "Mental Health First Aid", "Yoga Instructor Training", "Fitness Personal Trainer", "Healthcare Management", "Public Health Basics", "First Aid Certification", "Child Nutrition Specialist", "Elder Care Assistant", "Stress Management Techniques", "Meditation Instructor Course", "Sports Nutrition", "Health and Safety Compliance", "Medical Terminology", "Phlebotomy Technician", "Dental Assistant Training", "Pharmacology Basics", "Physical Therapy Assistant", "Holistic Health Practitioner", "Clinical Research Coordinator"]
}

INSTRUCTORS = {
    'Tech': ["Dr. Sarah Johnson", "Prof. Michael Chen", "Dr. James Wilson", "Ms. Lisa Rodriguez", "Mr. David Kim", "Dr. Emily Patel", "Prof. Robert Taylor", "Ms. Anna Schmidt"],
    'Business': ["Mr. John Smith", "Ms. Patricia Brown", "Dr. Robert Davis", "Prof. Jennifer Lee", "Mr. William Turner", "Ms. Elizabeth Grant", "Dr. Richard Freeman", "Prof. Susan Miller"],
    'Art': ["Ms. Maria Garcia", "Mr. Thomas Anderson", "Prof. Laura Martinez", "Ms. Christine Wong", "Mr. Daniel Lewis", "Ms. Rachel Green", "Prof. Anthony Clark", "Mr. Kevin Zhang"],
    'Health': ["Dr. Rebecca White", "Dr. Mark Thompson", "Prof. Nancy Harris", "Dr. Christopher Moore", "Ms. Karen Nelson", "Dr. Patricia Adams", "Prof. Joseph Hill", "Dr. Michelle Carter"]
}

DURATIONS = ["2 weeks", "3 weeks", "4 weeks", "6 weeks", "8 weeks", "10 weeks", "3 months", "6 months", "Self-paced (3 months)", "Weekend intensive", "5 days", "12 weeks"]
PRICE_RANGES = {'Tech': (49, 499), 'Business': (29, 399), 'Art': (19, 299), 'Health': (39, 449)}
DEFAULT_PRICE = (49, 499)

DESCRIPTION_TEMPLATES = [
    "This comprehensive {category} course covers {topic}. Perfect for beginners.",
    "Join our {duration} {category} program and master {topic} with hands-on projects.",
    "Learn {topic} from industry experts. Includes certification upon completion.",
    "Intensive {duration} training in {topic}. Boost your career prospects."
]

SYLLABUS_OUTLINES = {
    'Tech': ["Week 1-2: Intro\nWeek 3-4: Core\nWeek 5-6: Advanced\nWeek 7-8: Project"],
    'Business': ["Module 1-2: Fundamentals\nModule 3-4: Strategy\nModule 5-6: Implementation"],
    'Art': ["Lesson 1-2: Basics\nLesson 3-4: Techniques\nLesson 5-6: Portfolio"],
    'Health': ["Week 1-2: Principles\nWeek 3-4: Practice\nWeek 5-6: Certification"]
}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def safe_get_category():
    cats = [c[0] for c in TrainingCourse.Category.choices]
    return random.choice(cats) if cats else 'Tech'

def safe_get_format():
    fmts = [f[0] for f in TrainingCourse.Format.choices]
    return random.choice(fmts) if fmts else 'Online'

def safe_get_instructor(cat):
    return random.choice(INSTRUCTORS.get(cat, INSTRUCTORS['Tech']))

def safe_get_price(cat):
    min_p, max_p = PRICE_RANGES.get(cat, DEFAULT_PRICE)
    return round(random.uniform(min_p, max_p), 2)

def safe_get_title(cat):
    return random.choice(COURSE_TITLES.get(cat, COURSE_TITLES['Tech']))

def safe_get_syllabus(cat):
    return random.choice(SYLLABUS_OUTLINES.get(cat, SYLLABUS_OUTLINES['Tech']))

def get_enrollment_status(start, end, max_students=None, enrolled=0):
    today = timezone.now().date()
    if start > today:
        status = TrainingCourse.Enrollment.OPEN
    elif start <= today <= end:
        status = random.choice([TrainingCourse.Enrollment.OPEN, TrainingCourse.Enrollment.CLOSING_SOON])
    else:
        status = TrainingCourse.Enrollment.CLOSED
    
    # FIX: Only check capacity if max_students is not None
    if max_students is not None and max_students > 0:
        if enrolled >= max_students:
            status = TrainingCourse.Enrollment.CLOSED
        elif enrolled >= max_students * 0.9 and status != TrainingCourse.Enrollment.CLOSED:
            status = TrainingCourse.Enrollment.CLOSING_SOON
    return status

# ============================================================================
# MAIN FUNCTIONS
# ============================================================================
def create_training_courses(n=50):
    created = 0
    errors = []
    print(f"\n🚀 Creating {n} courses...")
    
    for i in range(n):
        try:
            cat = safe_get_category()
            title = f"{safe_get_title(cat)} {i+1}"
            
            today = timezone.now().date()
            start = today + timedelta(days=random.randint(-60, 90))
            duration = random.choice([2,4,6,8,10,12])
            end = start + timedelta(weeks=duration)
            
            has_max = random.random() < 0.7
            if has_max:
                max_stud = random.choice([20,25,30,35,40])
                enrolled = random.randint(0, max_stud)
            else:
                max_stud = None
                enrolled = random.randint(5, 50)
            
            course = TrainingCourse.objects.create(
                title=title[:200],
                course_code=f"{cat[:3].upper()}{random.randint(100,999)}",
                category=cat,
                description=f"Professional {cat} course: {title}. Perfect for career growth.",
                duration=random.choice(DURATIONS),
                format=safe_get_format(),
                enrollment=get_enrollment_status(start, end, max_stud, enrolled),
                max_students=max_stud,
                enrolled_students=enrolled,
                start_date=start,
                end_date=end,
                instructor=safe_get_instructor(cat),
                price=safe_get_price(cat),
                certificate_offered=random.random() > 0.3,
                syllabus=safe_get_syllabus(cat),
                prerequisites=f"Basic {cat} knowledge helpful."
            )
            created += 1
        except Exception as e:
            errors.append(f"Course {i+1}: {str(e)[:50]}")
        
        if (i+1) % 10 == 0:
            print(f"  Progress: {i+1}/{n}")
    
    print(f"\n✅ Created: {created}, Failed: {len(errors)}")
    if errors:
        print("First 3 errors:", errors[:3])
    print_course_stats()
    return created

def create_targeted_courses():
    courses = [
        {'title':'Full Stack Web Dev Bootcamp', 'code':'TECH101', 'cat':TrainingCourse.Category.TECH,
         'desc':'12-week bootcamp: HTML, CSS, JS, React, Node.js, MongoDB.', 'dur':'12 weeks',
         'fmt':TrainingCourse.Format.HYBRID, 'enroll':TrainingCourse.Enrollment.CLOSING_SOON,
         'max':25, 'enrolled':22, 'start':timezone.now().date()+timedelta(days=14),
         'end':timezone.now().date()+timedelta(days=98), 'instr':'Dr. Sarah Johnson',
         'price':2499, 'cert':True, 'syllabus':'Week 1-4: Frontend\nWeek 5-8: Backend\nWeek 9-12: Projects',
         'preq':'Basic computer skills'},
        
        {'title':'AWS Solutions Architect', 'code':'TECH202', 'cat':TrainingCourse.Category.TECH,
         'desc':'AWS certification prep with hands-on labs.', 'dur':'6 weeks',
         'fmt':TrainingCourse.Format.ONLINE, 'enroll':TrainingCourse.Enrollment.OPEN,
         'max':40, 'enrolled':15, 'start':timezone.now().date()+timedelta(days=30),
         'end':timezone.now().date()+timedelta(days=72), 'instr':'Prof. Michael Chen',
         'price':899, 'cert':True, 'syllabus':'Week 1: AWS Core\nWeek 2-3: Services\nWeek 4-6: Architecture',
         'preq':'Cloud basics'},
        
        {'title':'Digital Marketing Masterclass', 'code':'BUS101', 'cat':TrainingCourse.Category.BUSINESS,
         'desc':'SEO, social media, Google Ads, content strategy.', 'dur':'8 weeks',
         'fmt':TrainingCourse.Format.ONLINE, 'enroll':TrainingCourse.Enrollment.OPEN,
         'max':50, 'enrolled':32, 'start':timezone.now().date()+timedelta(days=7),
         'end':timezone.now().date()+timedelta(days=63), 'instr':'Ms. Patricia Brown',
         'price':799, 'cert':True, 'syllabus':'Week 1-2: SEO\nWeek 3-4: Social\nWeek 5-6: Ads\nWeek 7-8: Analytics',
         'preq':'None'},
        
        {'title':'PMP Certification Prep', 'code':'BUS202', 'cat':TrainingCourse.Category.BUSINESS,
         'desc':'Complete PMP exam preparation.', 'dur':'10 weeks',
         'fmt':TrainingCourse.Format.HYBRID, 'enroll':TrainingCourse.Enrollment.OPEN,
         'max':35, 'enrolled':28, 'start':timezone.now().date()+timedelta(days=21),
         'end':timezone.now().date()+timedelta(days=91), 'instr':'Dr. Richard Freeman',
         'price':1299, 'cert':True, 'syllabus':'Week 1-3: Framework\nWeek 4-7: Processes\nWeek 8-10: Exam Prep',
         'preq':'3+ years PM experience'},
        
        {'title':'Mental Health First Aid', 'code':'HEALTH101', 'cat':TrainingCourse.Category.HEALTH,
         'desc':'Certified Mental Health First Aid training.', 'dur':'2 days',
         'fmt':TrainingCourse.Format.OFFLINE, 'enroll':TrainingCourse.Enrollment.CLOSING_SOON,
         'max':20, 'enrolled':18, 'start':timezone.now().date()+timedelta(days=5),
         'end':timezone.now().date()+timedelta(days=7), 'instr':'Dr. Rebecca White',
         'price':299, 'cert':True, 'syllabus':'Day 1: Fundamentals\nDay 2: Intervention',
         'preq':'None'},
        
        {'title':'UX/UI Design Certificate', 'code':'ART101', 'cat':TrainingCourse.Category.ART,
         'desc':'Master Figma, prototyping, user research.', 'dur':'8 weeks',
         'fmt':TrainingCourse.Format.ONLINE, 'enroll':TrainingCourse.Enrollment.OPEN,
         'max':30, 'enrolled':12, 'start':timezone.now().date()+timedelta(days=10),
         'end':timezone.now().date()+timedelta(days=66), 'instr':'Ms. Maria Garcia',
         'price':699, 'cert':True, 'syllabus':'Week 1-2: Research\nWeek 3-4: Design\nWeek 5-6: Prototype\nWeek 7-8: Portfolio',
         'preq':'Creative mindset'}
    ]
    
    print(f"\n🚀 Creating {len(courses)} targeted courses...")
    created = 0
    for c in courses:
        try:
            TrainingCourse.objects.create(
                title=c['title'], course_code=c['code'], category=c['cat'],
                description=c['desc'], duration=c['dur'], format=c['fmt'],
                enrollment=c['enroll'], max_students=c['max'], enrolled_students=c['enrolled'],
                start_date=c['start'], end_date=c['end'], instructor=c['instr'],
                price=c['price'], certificate_offered=c['cert'], syllabus=c['syllabus'],
                prerequisites=c['preq']
            )
            created += 1
            print(f"  ✅ {c['title']}")
        except Exception as e:
            print(f"  ❌ {c['title']}: {str(e)[:50]}")
    
    print(f"\n✅ Created {created} targeted courses")
    return created

def create_bulk_training_courses(n=60):
    created = 0
    errors = 0
    print(f"\n🚀 Creating {n} bulk courses...")
    
    for i in range(n):
        try:
            cat = safe_get_category()
            title = f"{safe_get_title(cat)}-{random.randint(1000,9999)}"
            
            start = timezone.now().date() + timedelta(days=random.randint(-90, 120))
            duration = random.randint(2, 16)
            end = start + timedelta(weeks=duration)
            
            has_max = random.random() < 0.7
            if has_max:
                max_stud = random.choice([15,20,25,30,35,40])
                enrolled = random.randint(0, max_stud)
            else:
                max_stud = None
                enrolled = random.randint(5, 60)
            
            TrainingCourse.objects.create(
                title=title[:200],
                course_code=f"{cat[:3].upper()}{random.randint(100,999)}",
                category=cat,
                description=f"Professional {cat} training: {title}. Career advancement.",
                duration=f"{duration} weeks" if random.random()>0.3 else random.choice(DURATIONS),
                format=safe_get_format(),
                enrollment=get_enrollment_status(start, end, max_stud, enrolled),
                max_students=max_stud,
                enrolled_students=enrolled,
                start_date=start,
                end_date=end,
                instructor=safe_get_instructor(cat),
                price=safe_get_price(cat) * random.uniform(1, 2),
                certificate_offered=random.random() > 0.2,
                syllabus=safe_get_syllabus(cat),
                prerequisites=f"Basic {cat} knowledge helpful."
            )
            created += 1
        except Exception:
            errors += 1
        
        if (i+1) % 20 == 0:
            print(f"  Progress: {i+1}/{n} (Created: {created})")
    
    print(f"\n✅ Created: {created}, Failed: {errors}")
    print_course_stats()
    return created

def print_course_stats():
    total = TrainingCourse.objects.count()
    if total == 0:
        print("\n📊 No courses found")
        return
    
    print("\n" + "="*60)
    print("📊 TRAINING COURSE STATISTICS")
    print("="*60)
    print(f"\n📚 Total: {total}")
    
    for title, field in [('Category','category'), ('Status','status'), ('Format','format'), ('Enrollment','enrollment')]:
        print(f"\n{title}:")
        values = dict(getattr(TrainingCourse, title).choices if hasattr(TrainingCourse, title) else [])
        for val, label in values.items():
            count = TrainingCourse.objects.filter(**{field: val}).count()
            pct = (count/total)*100
            bar = "█" * int(pct/5) + "░" * (20 - int(pct/5))
            print(f"  {label:12}: {count:3} ({pct:5.1f}%) {bar}")
    
    print("\n" + "="*60)

def fix_enrollment_statuses():
    fixed = 0
    for c in TrainingCourse.objects.all():
        old = c.enrollment
        new = get_enrollment_status(c.start_date, c.end_date or c.start_date+timedelta(weeks=4), c.max_students, c.enrolled_students)
        if old != new:
            c.enrollment = new
            c.save()
            fixed += 1
    print(f"\n✅ Fixed {fixed} courses")
    return fixed

def clear_all_courses():
    count = TrainingCourse.objects.count()
    if count == 0:
        print("📊 No courses to delete")
        return
    if input(f"Delete {count} courses? (yes/no): ").lower() == 'yes':
        TrainingCourse.objects.all().delete()
        print(f"✅ Deleted {count} courses")

# For direct execution
if __name__ == "__main__":
    while True:
        print("\n1: Random (50)\n2: Targeted (6)\n3: Bulk (60)\n4: Stats\n5: Fix\n6: Clear\n7: Exit")
        c = input("Choice: ")
        if c=='1': create_training_courses(50)
        elif c=='2': create_targeted_courses()
        elif c=='3': create_bulk_training_courses(60)
        elif c=='4': print_course_stats()
        elif c=='5': fix_enrollment_statuses()
        elif c=='6': clear_all_courses()
        elif c=='7': break
