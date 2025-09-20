

#from .models import Activity, Category , Department


#Interview description data
Department=[

{
	'id':'1',
	'Department':'coordinator',
},

{
    'id':'2',
	'Department':'HR',
},

]

def departments (request):
    return {
       # 'departments': Department.objects.all()
        #'departments': Department
    }

def categories(request):
    return {
        #'categories': Category.objects.all()
      #'categories': Category.objects.filter(level=0)
      #'categories': Category.objects.filter(level=1)
    }

def activities(request):
    return {
       # 'activities': Activity.objects.all()
    }

