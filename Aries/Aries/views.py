#encoding=utf8
from django.db.models import Q
import logging
ac_logger = logging.getLogger("access_log")
from django.contrib.auth.models import User
from django.contrib.auth import login as auth_login,logout as auth_logout,authenticate
from django import forms
from django.shortcuts import render,render_to_response,redirect
import json
from django.http import HttpResponse
from user_auth.models import *
from ldap_client import ldap_get_vaild
from django.views.decorators.csrf import ensure_csrf_cookie

#@ensure_csrf_cookie
def login(request):
    ac_logger.info("######################cookie: {0}#######".format(request.COOKIES.get('csrftoken')))
    ac_logger.info("######################login#######")
    if request.method == "POST":
        res = {}
        username = request.POST.get("username")
        password = request.POST.get("password")
        email = username + "@baifendian.com"
        ldap_user = ldap_get_vaild(username=username,passwd=password)
        ac_logger.info("######################login####### %s" %ldap_user)
        if ldap_user:
            user = authenticate(username=username, password=password)
            if not user:
                userAdd=User.objects.create_user(username, email, password)  
                userAdd.is_active=True  
                userAdd.save
                user = authenticate(username=username, password=password)
            is_admin = 0
            cur_space = ""
            if user:
                auth_login(request, user)
                try:
                    account = Account.objects.get(name=username)
                    spaceUserRole = SpaceUserRole.objects.filter(user=account)
                    if spaceUserRole:
                        if spaceUserRole[0].role.name.upper() in ["SUPERADMIN","SPACEADMIN"]:
                            is_admin = 1
                        else:
                            is_admin = 0
                        account.cur_space=spaceUserRole[0].space.name
                        account.save()
                        cur_space = account.cur_space
                except Exception,e:
                    ac_logger.error(e)
                    account = Account(name=username,password=password,email=email,is_active=1)
                    account.role = Role.objects.get(name="guest")
                    account.save()
                ac_logger.info("###login##return_data:is_admin=%s,cur_space=%s" %(is_admin,cur_space))
                    
                res["code"] = 200
                res["data"] = {"name":username,"type":is_admin,"cur_space":cur_space}
            else:
                res["code"] = 500
                res["data"] = "username or password is error"
            response = HttpResponse(content_type='application/json')
            response.write(json.dumps(res))
            response.set_cookie('csrftoken',request.COOKIES.get('csrftoken'))
            response["Access-Control-Allow-Origin"] = "*"
            response["Access-Control-Allow-Methods"] = "POST,GET,PUT, DELETE"
            return response
        else:
            res["code"] = 500
            res["data"] = "username or password is error"
            response = HttpResponse(content_type='application/json')
            response.write(json.dumps(res))
            response["Access-Control-Allow-Origin"] = "*"
            response["Access-Control-Allow-Methods"] = "POST,GET,PUT, DELETE"
            return response
    else:
        user = request.user
        ac_logger.info("----------------user:%s" %user)
        if user:
            username = user.username
            try:
                account = Account.objects.get(name=username)
                if not account.cur_space:
                    spaceUserRole = SpaceUserRole.objects.filter(user=account)
                    account.cur_space=spaceUserRole[0].space.name
                    account.save()
                user = {"name":username,"type":1,"cur_space":account.cur_space}
            except Exception,e:
                ac_logger.error(e)
                user = ""
        else:
            user = ""
        user = json.dumps(user)
        ac_logger.info("##########user:%s" %user)   
        response =  render_to_response('index/index.html',locals())
        # set default cookie value
        response.set_cookie('csrftoken',request.COOKIES.get('csrftoken','S6ouKsk1kRrp5qsHlmd5fupVJewYitW3'))
        return response

def logout(request):
    result = {}
    try:
        auth_logout(request)
        result["code"] = 200
        result["data"] = "logout success."
    except Exception,e:
        ac_logger.error(e)
        result["code"] = 500
        result["data"] = "logout failed."
    response = HttpResponse(content_type='application/json')
    response.write(json.dumps(result))
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "POST,GET,PUT, DELETE"
    return response

@ensure_csrf_cookie
def index(request):
    ac_logger.info("######################cookie: {0}#######".format(request.COOKIES.get('csrftoken')))
    #save cur_space
    user = request.user
    cur_space = request.GET.get("cur_space","")
    if user:
        username = user.username
        try:
            account = Account.objects.get(name=username)
            if not cur_space:
                cur_space = account.cur_space
            user = {"name":username,"type":1,"cur_space":cur_space}
        except Exception,e:
            ac_logger.error(e)
            user = ""
    else:
        user = ""
    user = json.dumps(user)
    return render_to_response('index/index.html',locals())
