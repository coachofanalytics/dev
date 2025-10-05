import  os
import  logging
logger = logging.getLogger(__name__)

from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from gapi.gservices import get_service, search_messages, get_message, cashapp_main
from mail.custom_email import send_reply
from ai_services.models import CashappMail, ReplyMail


def parse_mail(request):
    search_query = 'from:cash@square.com is:unread'
    # search_query = 'from:cash@square.com after:2022/9/1'

    service = get_service()  # default service with default scope, gmail-v1
    
    if not service:
        return HttpResponse('No service!')

    search_results = search_messages(service, search_query)
    print(f'START PROCESS',search_results)
    search_results_len = len(search_results)
    logger.debug(f'search_results_len: {search_results_len}')

    if not search_results:
        message=f'No results found.Please Try again later!'
        # return HttpResponse('No results found!')
        # return redirect('main:noresult')
        return render(request,'main/snippets_templates/interview_snippets/result.html',{"message":message})

    for result in search_results:
        msg_dict = get_message(service=service, msg_id=result.get('id'))
        # print(f'msg_dict: {msg_dict}')
        # logger.debug(f'msg_dict: {msg_dict}')
        '''Reading and writing the files'''
        # folderpath = r"gapi\stored_mails"
        # coda\gapi\stored_mails
        folderpath ='gapi/stored_mails'
        filepaths  = [os.path.join(folderpath, name) for name in os.listdir(folderpath)]
        # print("MY CASHAPP FUNCTION",filepaths)
        for path in filepaths:
            # print("PATH=====>",path)
            cashapp_data = cashapp_main(path=path)
            os.remove(path)
            # print(f"Amount : {cashapp_data['Amount']}")
            # print(f"From : {cashapp_data['From']}")
            from_mail = cashapp_data['From']
            to_mail = cashapp_data['To']
            if from_mail == 'None':
                continue

            try:
                CashappMail.objects.create(
                    id=msg_dict.get('id'),
                    # from_mail=msg_dict.get('from_mail'),
                    from_mail = cashapp_data['From'],
                    to_mail = to_mail,
                    subject=msg_dict.get('subject'),
                    amount = cashapp_data['Amount'],
                    destination = 'cashapp',
                    file_name=msg_dict.get('file_name'),
                    full_path=msg_dict.get('full_path'),
                    text_mail=msg_dict.get('text_mail'),
                    received_date=msg_dict.get('received_date')
                )
            except Exception as e:
                logger.error('error on adding new record!')
                logger.error('error msg is ' + str(e))
                logger.error(f'msg id is: msg_dict.get("id")')
                # return HttpResponse("Error on createing a record!")
    message=f' {search_results_len} results were/was found and processed!'
    # context={
    #     # "results": search_results_len
    #     "message":message

    # }
    # return HttpResponse(f'{search_results_len} results processed!')
    return render(request,'main/snippets_templates/interview_snippets/result.html',{"message":message})
    
def search_job_mail(request):

    mails = ReplyMail.objects.all()
    return render(request, "ai_services/Repliedmail.html", {'mails': mails})

    # search_results=[]
    # search_query = ['jobs role', 'hiring', 'recruitment']
    # # search_query = 'ranjeetgup19@gmail.com is:unread'
    # service = get_service()  # default service with default scope, gmail-v1
    # if not service:
    #     return HttpResponse('No service!')
    # for search in search_query:
    #     se=search+" is:unread"
    #     search_results += search_messages(service, se)
    #
    # # search_results += search_messages(service, search_query)
    # # search_results_len = len(search_results)
    #
    # if not search_results:
    #     # return HttpResponse('No results found!')
    #     mails = ReplyMail.objects.all()
    #     return render(request, "ai_services/Repliedmail.html", {'mails': mails, 'msg': "no new result found"})
    #     # return redirect('main:noresult')
    #     # return render(request,'main/snippets_templates/interview_snippets/result.html',{"message":message})
    #
    # for result in search_results:
    #     try:
    #         msg_dict = send_reply(service=service, msg_id=result.get('id'), request=request)
    #         if msg_dict:
    #             try:
    #                 ReplyMail.objects.create(
    #                     id=msg_dict.get('id'),
    #                     from_mail=msg_dict.get('from_mail'),
    #                     to_mail=msg_dict.get('to_mail'),
    #                     subject=msg_dict.get('subject'),
    #                     text_mail=msg_dict.get('text_mail'),
    #                     received_date=msg_dict.get('received_date')
    #                 )
    #             except Exception as e:
    #                 logger.error('error on adding new record!')
    #                 logger.error('error msg is ' + str(e))
    #                 logger.error(f'msg id is: msg_dict.get("id")')
    #     except:
    #         mails = ReplyMail.objects.all()
    #         return render(request, "ai_services/Repliedmail.html", {'mails': mails})
    # mails = ReplyMail.objects.all()
    # return render(request, "ai_services/Repliedmail.html", {'mails': mails})


 