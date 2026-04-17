from django.shortcuts import render,redirect
from .models import Taskmodel 
from .forms import TaskForm

# Create your views here.

def TaskList(request):
    tasks = Taskmodel.objects.all()
    return render(request,'taskapp/task_list.html',{'tasks':tasks})



def TaskCreate(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/taskapp/tasklist')
    else:
        form = TaskForm()
    return render(request,'taskapp/task_Form.html',{'form':form})