from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
import json
from .models import *
import datetime
import time

@csrf_exempt
def sign_in(request):
    data = request.body.decode()
    ip = request.META.get('REMOTE_ADDR', '') or request.META.get('HTTP_X_FORWARDED_FOR', '')
    try:
        session = Sessions.objects.get(ip=ip)
        session.delete()
    except:
        pass
    data = json.loads(data)
    login = data["login"]
    password = data["password"]
    try:
        user = User.objects.get(username=login)
    except:
        return JsonResponse({"message": "wrong login"})
    if user.password == password:
        session = Sessions(user=user,
                           ip=ip
                           )
        session.save()
        try:
            m = list(Messages.objects.filter(id_user=user))
            session.chat = str(m[0].id_chat.id)
            session.save()
        except:
            pass
        return JsonResponse({"message":"0"})
    else:
        return JsonResponse({"message": "wrong password"})

def sign_in_view(request):
    return render(request, "chats/signin.html", {})

@csrf_exempt
def sign_up(request):
    data = request.body.decode()
    data = json.loads(data)
    email = data["email"]
    login = data["login"]
    password = data["password"]
    try:
        user = User.objects.get(username=login, password=password)

        return JsonResponse({"message": "login already used"})
    except:
        try:
            user = User.objects.get(email=email)
            return JsonResponse({"message":"email already used"})
        except:
            user = User(username=login,
                        email=email,
                        password=password)
            user.save()
            return JsonResponse({"message":"0"})

def sign_up_view(request):
    return render(request, "chats/signup.html", {})

@csrf_exempt
def sign_out(request):
    ip = request.META.get('REMOTE_ADDR', '') or request.META.get('HTTP_X_FORWARDED_FOR', '')
    try:
        session = Sessions.objects.get(ip=ip)
    except:
        return JsonResponse({"":"not deleted"})
    session.delete()
    return JsonResponse({"":"deleted"})

def chat_view(request):
    return render(request, "chats/chat.html", {})

@csrf_exempt
def add_chat(request):
    data = request.body.decode()
    ip = request.META.get('REMOTE_ADDR', '') or request.META.get('HTTP_X_FORWARDED_FOR', '')
    data = json.loads(data)
    name = data["name"]
    try:
        session = Sessions.objects.get(ip=ip)
    except:
        return redirect('/sign_in')
    user = session.user
    ch = Chats(name=name)
    ch.save()
    ch_us = Chats_Users(
        id_chat=ch,
        id_user=user
    )
    ch_us.save()
    return JsonResponse({"id":str(ch.id)})

@csrf_exempt
def get_chats(request):
    ip = request.META.get('REMOTE_ADDR', '') or request.META.get('HTTP_X_FORWARDED_FOR', '')
    try:
        session = Sessions.objects.get(ip=ip)
    except:
        return JsonResponse({"errorMessage":"0"})
    user = session.user
    resp = []
    for ch_us in Chats_Users.objects.filter(id_user=user):
        chat = ch_us.id_chat
        name = chat.name
        id=str(chat.id)
        try:
            message = list(Messages.objects.filter(id_chat=chat.id))
        except:
            message = None
        if (message != None and len(message)>0):
            message = message[len(message)-1]
            last_message_text = message.text
            if str(user.id) in message.us_check.split():
                last_message_status = "checked"
            else:
                last_message_status = "unchecked"
            u = message.id_user
            last_message_user = u.username
        else:
            last_message_text = ""
            last_message_status = ""
            last_message_user = ""

        cht = {
            "id": id,
            "name": name,
            "last_message_text": last_message_text,
            "last_message_status": last_message_status,
            "last_message_user": last_message_user
        }
        resp.append(cht)
    return JsonResponse({"chats":resp})

@csrf_exempt
def add_message(request):
    ip = request.META.get('REMOTE_ADDR', '') or request.META.get('HTTP_X_FORWARDED_FOR', '')
    try:
        session = Sessions.objects.get(ip=ip)
    except:
        return redirect('/sign_in')
    data = request.body.decode()
    data = json.loads(data)
    text = data["text"]
    user = session.user
    time = datetime.datetime.now()
    time = str(time.hour) + "." +str(time.minute)
    message = Messages(
        id_chat = Chats.objects.get(id=int(session.chat)),
        id_user = user,
        text = text,
        time = time
    )
    message.save()
    return JsonResponse({"message":"allright"})

@csrf_exempt
def add_user_to_chat(request):
    ip = request.META.get('REMOTE_ADDR', '') or request.META.get('HTTP_X_FORWARDED_FOR', '')
    try:
        session = Sessions.objects.get(ip=ip)
    except:
        return redirect('/sign_in')
    data = request.body.decode()
    data = json.loads(data)
    login = data["login"]
    chat_id = data["chat_id"]
    try:
        chat = Chats.objects.get(id=int(chat_id))
    except:
        return JsonResponse({"message" : "error1"})
    user = session.user
    try:
        ch_us = Chats_Users.objects.get(id_user=user, id_chat=chat)
    except:
        return JsonResponse({"message": "error2"})
    try:
        user2 = User.objects.get(username=login)
    except:
        return JsonResponse({"message": "user does not exist"})
    try:
        ch_us = Chats_Users.objects.get(id_user=user2, id_chat=chat)
        return JsonResponse({"message": "user already in chat"})
    except:
        pass
    ch_us = Chats_Users(
        id_user=user2,
        id_chat=chat
    )
    ch_us.save()
    return JsonResponse({"message": "all right"})

@csrf_exempt
def get_messages(request):
    ip = request.META.get('REMOTE_ADDR', '') or request.META.get('HTTP_X_FORWARDED_FOR', '')
    try:
        session = Sessions.objects.get(ip=ip)
    except:
        return redirect('/sign_in')

    try:
        m = Messages.objects.filter(id_chat=Chats.objects.get(id=int(session.chat)))
    except:
        m = []
    resp = []
    for mess in m:
        us = mess.id_user
        my = (us == session.user)
        message_resp = {
                            "text": mess.text,
                            "user": us.username,
                            "time": mess.time,
                            "my": str(my)
                        }
        resp.append(message_resp)
        if not mess.checked:
            s = mess.us_check
            if not (str(session.user.id) in s.split()):
                mess.us_check += " " + str(session.user.id)
                mess.save()
                s = mess.us_check
                if len(s.split()) == Chats_Users.objects.filter(id_chat = Chats.objects.get(id=int(session.chat))).count():
                    mess.checked = True
                    mess.save()
    if session.chat != "":
        chat = Chats.objects.get(id=int(session.chat))
        name = chat.name
    else:
        name = ""
    return JsonResponse({"messages": resp,
                         "name_chat": name})

@csrf_exempt
def get_unchecked_messages(request):
    ip = request.META.get('REMOTE_ADDR', '') or request.META.get('HTTP_X_FORWARDED_FOR', '')
    try:
        session = Sessions.objects.get(ip=ip)
    except:
        return redirect('/sign_in')
    user = session.user

    if session.chat != "":
        chat=Chats.objects.get(id=int(session.chat))
    else:
        return JsonResponse({"message":"ch ne vibran"})
    um = []
    start = time.monotonic()
    now = time.monotonic()
    x = 0
    while ((um == None or list(um) == []) and x<60):
        try:
            um = list(Messages.objects.filter(checked=False,id_chat=chat))#Chats.objects.get(id=int(session.chat))))
        except:
            um = []
        if um != []:
            resp = []
            for mes in um:
                s = mes.us_check
                if not (str(session.user.id) in s.split()):
                    mes.us_check += " " + str(session.user.id)
                    mes.save()
                    us = mes.id_user
                    my = (us == user)
                    un_mes = {
                        "text": mes.text,
                        "user": us.username,
                        "time": mes.time,
                        "my": str(my)
                    }
                    resp.append(un_mes)
                    s = mes.us_check
                    if len(s.split()) == Chats_Users.objects.filter(id_chat=chat).count():
                        mes.checked = True
                        mes.save()
                else:
                    um = []
            if resp != []:
                return JsonResponse({"messages":resp})
        now = time.monotonic()
        x= '{:>9.2f}'.format(now - start)
        x = float(x)
    return JsonResponse({"messages":[]})

@csrf_exempt
def add_num_chat(request):
    ip = request.META.get('REMOTE_ADDR', '') or request.META.get('HTTP_X_FORWARDED_FOR', '')
    try:
        session = Sessions.objects.get(ip=ip)
    except:
        return redirect('/sign_in')
    data = request.body.decode()
    data = json.loads(data)
    session.chat = data["id"]
    session.save()
    return JsonResponse({"message":"all right"})