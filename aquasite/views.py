from django.shortcuts import render, redirect

from django.urls import reverse

from django.http import HttpResponse, JsonResponse

from django.core.mail import send_mail

from decouple import config

import pyrebase, random, string, json


firebaseConfig = {
  'apiKey': config('FIREBASE_API_KEY'),
  'authDomain': config('FIREBASE_AUTH_DOMAIN'),
  'databaseURL': config('FIREBASE_DATABASE_URL'),
  'projectId': config('FIREBASE_PROJECT_ID'),
  'storageBucket': config('FIREBASE_STORAGE_BUCKET'),
  'messagingSenderId': config('FIREBASE_MESSAGING_SENDER_ID'),
  'appId': config('FIREBASE_APP_ID')
}

firebase = pyrebase.initialize_app(firebaseConfig)
database = firebase.database()
auth = firebase.auth()

userId = None

def home(request):
  return render(request, 'aquasite/pages/home.html')

def aboutUs(request):
  return render(request, 'aquasite/pages/about-us.html')

def contact(request):
  return render(request, 'aquasite/pages/contact.html')

class userAuth:
  def auth(request):
    return render(request, 'aquasite/pages/auth.html')
  
  def login(request):
    global userId
    email = request.POST.get('login-email')
    password = request.POST.get('login-password')
    try:
      user = auth.sign_in_with_email_and_password(email, password)
      userId = user['localId']
      return redirect('dashboard')
    except:
      return redirect('auth')
    
  class userRegister:
    def codeGenerator(length=5, caracteres=string.digits):
      return ''.join(random.choice(caracteres) for _ in range(length))

    name = None
    email = None
    password = None
    code = codeGenerator()
    
    def verification(request):
      if request.META.get('HTTP_REFERER', '').endswith('/authentication/'):
        userAuth.userRegister.name = request.POST.get('register-name')
        userAuth.userRegister.email = request.POST.get('register-email')
        userAuth.userRegister.password = request.POST.get('register-password')
        send_mail(
          'AQUA - Código de verificação de email',
          f'Opa, {userAuth.userRegister.name}! \nSeu código de verificação é: {userAuth.userRegister.code}',
          'aquaseaware@gmail.com',
          [userAuth.userRegister.email],
          fail_silently=False,
        )
      return render(request, 'aquasite/pages/verification.html')

    def register(request):
      global userId
      inputCode = request.POST.get('verification-code-input')
      emailCode = userAuth.userRegister.code
      if inputCode == emailCode:
        try:
          user = auth.create_user_with_email_and_password(
            userAuth.userRegister.email, 
            userAuth.userRegister.password
            )
          userId = user['localId']
          userData = {
            'name': userAuth.userRegister.name,
            'email': userAuth.userRegister.email
          }
          database.child('UsersData').child(userId).update(userData)
          return redirect('dashboard')
        except:
          return redirect('verification')
      elif inputCode != emailCode:
        return redirect('verification')
  
class userDashboard:
  def dashboard(request):
    modules = database.child('UsersData').child(userId).child('modules').get().val()
    if modules != None:
      context = {
        'modules': modules.items(),
      }
      return render(request, 'aquasite/pages/dashboard.html', context)
    else:
      return render(request, 'aquasite/pages/dashboard.html')

  def module(request, moduleId):
    def module():
      return database.child('UsersData').child(userId).child('modules').child(moduleId)

    moduleData = module().get().val()
    if 'name' in moduleData:
      moduleName = moduleData['name']
    elif 'name' not in moduleData:
      moduleName = request.POST.get('module-name')
      module().update({'name': moduleName})

    aquariumHeight = False
    if 'aquariumHeight' in moduleData:
      aquariumHeight = True


    class phLevel:
      def __init__(self, color, number):
        self.color = color
        self.number = number
    phLevels = [
      phLevel('#FF0000', 0),
      phLevel('#FF4C00', 1),
      phLevel('#FF8000', 2),
      phLevel('#FFB84C', 3),
      phLevel('#FFD699', 4),
      phLevel('#FFFF66', 5),
      phLevel('#FFFF00', 6),
      phLevel('#D4FF00', 7),
      phLevel('#A0FF00', 8),
      phLevel('#66FF00', 9),
      phLevel('#33FF66', 10),
      phLevel('#00FF99', 11),
      phLevel('#00FFFF', 12),
      phLevel('#0099FF', 13),
      phLevel('#0033FF', 14)
    ]

    context = {
      'moduleId': moduleId,
      'moduleName': moduleName,
      'aquariumHeight': aquariumHeight, 
      'phLevels': phLevels,
    }
    return render(request, 'aquasite/pages/module.html', context)
  
  def saveAquariumHeight(request, moduleId):
    if request.method == 'POST':
      aquariumHeight = request.POST.get('aquarium-height')
      database.child('UsersData').child(userId).child('modules').child(moduleId).child('aquariumHeight').set(aquariumHeight)
    
    return redirect(reverse('module', kwargs={'moduleId': moduleId}))

  def reports(request):
    return render(request, 'aquasite/pages/reports.html')

  def account(request):
    name = database.child('UsersData').child(userId).child('name').get().val()
    email = database.child('UsersData').child(userId).child('email').get().val()
    modules = database.child('UsersData').child(userId).child('modules').get().val()
    profilePicUrl = database.child('UsersData').child(userId).child('profilePicUrl').get().val()
    if modules != None:
      modules = len(list(modules.keys()))
    elif modules == None:
      modules = 0

    if profilePicUrl == None:
      profilePicUrl = '../../../static/aquasite/images/gray.jpg'

    context = {
      'name': name,
      'email': email,
      'modules': modules,
      'profilePicUrl': profilePicUrl,
    }
    return render(request, 'aquasite/pages/account.html', context)

  def saveProfilePic(request):
    global userId
    if request.method == 'POST':
      try:
        profile_pic_url = request.POST.get('profile-pic-url')
        database.child('UsersData').child(userId).update({'profilePicUrl': profile_pic_url})
        return redirect('account')
      except json.JSONDecodeError:
        return JsonResponse({'error': 'Dados inválidos.'}, status=400)
    else:
      return JsonResponse({'error': 'Método não permitido.'}, status=405)
      
  