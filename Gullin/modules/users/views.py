import json
# import base64
import requests

from django.utils import timezone
from django.db.utils import IntegrityError
from django.contrib.gis.geoip2 import GeoIP2
from django.conf import settings
from django.contrib.auth.hashers import check_password

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework.decorators import api_view

from Gullin.utils.rest_framework_jwt.serializers import JSONWebTokenSerializer, RefreshJSONWebTokenSerializer
from Gullin.utils.rest_framework_jwt.settings import api_settings as jwt_settings

from Gullin.utils.get_client_ip import get_client_ip
from Gullin.utils.country_code import country_utils
from Gullin.utils.send.email import send_email
from Gullin.utils.send.sms import send_sms

from .serializers import CreateUserSerializer, FullIDVerificationSerializer, FullInvestorUserSerializer, FullUserLogVerificationSerializer, FullCompanyUserSerializer
from .models import InvestorUser, User, InvestorUserAddress, UserLog, IDVerification
from ..wallets.models import Wallet


class UserAuthViewSet(viewsets.ViewSet):
	"""
	The viewset for user authentication, includes sign_up, log_in, log_out, and verification
	"""
	parser_classes = (FormParser, JSONParser)
	permission_classes = (AllowAny,)

	def sign_up(self, request):
		# Get user login IP and add to data
		data = request.data.copy()
		data['last_login_ip'] = get_client_ip(request)

		# Create user instance using serializer
		serializer = CreateUserSerializer(data=data)
		serializer.is_valid(raise_exception=True)
		user = serializer.save()

		# All User created through this method is investor,
		# so we should create a InvestorUser instance and bind to new created User
		investor = InvestorUser.objects.create(first_name=request.data.get('first_name'),
		                                       last_name=request.data.get('last_name'))
		user.investor = investor
		user.save()

		# All InvestorUser has a insite wallet,
		# so we should create a Wallet instance and bind to new created InvestorUser
		# IMPORTANT: since the public/private key pair is generated on the frontend, it will be stored to database later
		wallet = Wallet.objects.create(investor_user=investor)
		# Init Balance objects and add to wallet
		wallet.init_balance()

		# Send user verification email when user register
		verification_code = user.verification_code
		verification_code.refresh()
		ctx = {
			'user_full_name'   : investor.full_name,
			'verification_code': verification_code.code,
			'user_email'       : user.email
		}
		send_email([user.email], 'Gullin - Welcome! Please Verify Your Email', 'welcome_and_email_verification', ctx)

		# Get user auth token
		payload = jwt_settings.JWT_PAYLOAD_HANDLER(user)
		token = jwt_settings.JWT_ENCODE_HANDLER(payload)

		# Construct response object to set cookie
		serializer = FullInvestorUserSerializer(user.investor)
		response = Response(serializer.data, status=status.HTTP_201_CREATED)
		response.set_cookie(jwt_settings.JWT_AUTH_COOKIE,
		                    token,
		                    expires=(timezone.now() + jwt_settings.JWT_EXPIRATION_DELTA),
		                    httponly=True)
		return response

	def log_in(self, request):
		# Login Attempt
		if request.method == 'POST':
			# Try login
			serializer = JSONWebTokenSerializer(data=request.data)
			# If login successful
			if serializer.is_valid():
				# get user instance and ip
				user = serializer.object.get('user')
				auth_token = serializer.object.get('token')
				user_ip = get_client_ip(request)

				# if user logged in form a old ip
				if user_ip == user.last_login_ip:
					# Update user last login timestamp and last login IP
					user.update_last_login()
					user.update_last_login_ip(user_ip)

					# Generate Log
					UserLog.objects.create(user_id=user.id,
					                       ip=user_ip,
					                       action='Login Successful',
					                       device=request.META['HTTP_USER_AGENT'])
					# Generate Response
					# Add user to the response data
					if user.is_investor:
						serializer = FullInvestorUserSerializer(user.investor)
					elif user.is_company_user:
						serializer = FullCompanyUserSerializer(user.company_user)

					response_data = serializer.data
					response_data['data'] = 'success'
					response = Response(response_data, status=status.HTTP_200_OK)
					# Add cookie to the response data
					response.set_cookie(jwt_settings.JWT_AUTH_COOKIE,
					                    auth_token,
					                    expires=(timezone.now() + jwt_settings.JWT_EXPIRATION_DELTA),
					                    httponly=True)
					return response

				# else if user logged in from a new ip, go to 2 factor auth
				# Save user and token to session
				request.session['user_id'] = user.id
				request.session['auth_token'] = serializer.object.get('token')

				# Start 2 factor auth code
				# If user not enabled TOTP
				if not user.TOTP_enabled:
					# Make sure user has phone number
					if user.phone:
						# Refresh code
						user.verification_code.refresh()
						# Send sms
						phone_num = user.phone_country_code + user.phone
						send_sms(phone_num,
						         'Verification Code: ' + user.verification_code.code + '\nInvalid in 5 minutes.')
						msg = {'data': 'We have sent a verification code to your phone, please verify.'}
					# Else send 2-factor to users email
					else:
						# Refresh code
						user.verification_code.refresh()
						# Send email
						verification_code = user.verification_code
						verification_code.refresh()
						ctx = {
							'user_full_name'   : user.investor.full_name,
							'verification_code': verification_code.code,
							'user_email'       : user.email
						}
						send_email([user.email], 'Gullin - Verification Code', 'verification_code', ctx)

						msg = {'data': 'We have sent a verification code to your email, please verify.'}
				# If user enabled TOTP
				else:
					# TODO: work with TOTP clients
					msg = {'data': 'Please verify using your 2 factor authenticator.'}
					pass

				# Generate Log
				UserLog.objects.create(user_id=user.id,
				                       ip=get_client_ip(request),
				                       action='Login Successful (Need 2 Factor Auth)',
				                       device=request.META['HTTP_USER_AGENT'])
				# Send Warning Email
				g = GeoIP2()
				try:
					city = g.city(user_ip)
					location = city.get('city') + ', ' + city.get('country_name')
				except:
					location = 'Unknown'
				ctx = {
					'user_full_name': user.investor.full_name,
					'user_email'    : user.email,
					'user_ip'       : user_ip,
					'user_location' : location,
					'user_device'   : request.META['HTTP_USER_AGENT'],
				}
				send_email([user.email], 'Gullin - Login from a different IP', 'different_ip_login_notice', ctx)

				return Response(msg, status=status.HTTP_200_OK)
			else:
				return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

		# Verify 2 Factor code
		elif request.method == 'PATCH':
			# check session
			if request.session.get('user_id') and request.session.get('auth_token'):
				# retrieve data from session
				user = User.objects.get(id=request.session['user_id'])
				token = request.session['auth_token']

				# Check verifications code
				# If user not enabled TOTP
				if not user.TOTP_enabled:
					verification_code = user.verification_code
					# Check If code is valid
					if verification_code.is_expired:
						return Response({'error': 'Verification code expired, please request another code.'},
						                status=status.HTTP_400_BAD_REQUEST)
					if not (request.data.get('verification_code') == verification_code.code):
						return Response({'error': 'Verification code doesn\'t match, please try again or request another code.'},
						                status=status.HTTP_400_BAD_REQUEST)
					# Verification code is valid, so expire verification code
					verification_code.expire()

				# If user enabled TOTP
				else:
					# TODO: work with TOTP clients
					pass

				# Code is valid

				# Clear session
				del request.session['auth_token']
				del request.session['user_id']
				user_ip = get_client_ip(request)

				# Update user last login timestamp and last login IP
				user.update_last_login()
				user.update_last_login_ip(user_ip)

				# Generate Log
				UserLog.objects.create(user_id=user.id,
				                       ip=user_ip,
				                       action='2 Factor Auth Successful',
				                       device=request.META['HTTP_USER_AGENT'])

				# Generate Response
				# Add user to the response data
				if user.is_investor:
					serializer = FullInvestorUserSerializer(user.investor)
				elif user.is_company_user:
					serializer = FullCompanyUserSerializer(user.company_user)

				response = Response(serializer.data, status=status.HTTP_200_OK)
				# Add cookie to the response data
				response.set_cookie(jwt_settings.JWT_AUTH_COOKIE,
				                    token,
				                    expires=(timezone.now() + jwt_settings.JWT_EXPIRATION_DELTA),
				                    httponly=True)
				return response
			else:
				return Response({'error': 'You have to login first!'}, status=status.HTTP_400_BAD_REQUEST)

	def log_out(self, request):
		response = Response()
		response.delete_cookie('gullin_jwt')
		return response

	def refresh(self, request):
		data = request.data.copy()
		data['token'] = request.COOKIES.get(jwt_settings.JWT_AUTH_COOKIE)

		serializer = RefreshJSONWebTokenSerializer(data=data)

		if serializer.is_valid():
			user = serializer.object.get('user') or request.user
			token = serializer.object.get('token')

			# Generate Response
			# Add user to the response data
			if user.is_investor:
				serializer = FullInvestorUserSerializer(user.investor)
			elif user.is_company_user:
				serializer = FullCompanyUserSerializer(user.company_user)

			response = Response(serializer.data, status=status.HTTP_200_OK)
			# Add cookie to the response data
			response.set_cookie(jwt_settings.JWT_AUTH_COOKIE,
			                    token,
			                    expires=(timezone.now() + jwt_settings.JWT_EXPIRATION_DELTA),
			                    httponly=True)
			return response

		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

	def forget_password(self, request):
		if request.method == 'GET':
			# Send code
			email_or_phone = request.query_params.get('u')
			if not email_or_phone:
				return Response({'error': 'Must provide email or phone.'}, status=status.HTTP_400_BAD_REQUEST)

			user = User.objects.filter(email=email_or_phone)
			# email
			if user:
				user = user[0]
				user.verification_code.refresh()
				request.session['user_id'] = user.id
				# Send email
				verification_code = user.verification_code
				verification_code.refresh()
				ctx = {
					'user_full_name'   : user.investor.full_name,
					'verification_code': verification_code.code,
					'user_email'       : user.email
				}
				send_email([user.email], 'Gullin - Verification Code', 'verification_code', ctx)

				UserLog.objects.create(user_id=user.id,
				                       ip=get_client_ip(request),
				                       action='Forgot password request',
				                       device=request.META['HTTP_USER_AGENT'])

				msg = {'data': 'We have sent a verification code to your email, please verify.'}
				return Response(msg, status=status.HTTP_200_OK)
			# phone
			user = User.objects.filter(phone=email_or_phone)
			if user:
				user = user[0]
				user.verification_code.refresh()
				request.session['user_id'] = user.id
				# Send sms
				phone_num = user.phone_country_code + user.phone
				send_sms(phone_num,
				         'Verification Code: ' + user.verification_code.code + '\nInvalid in 5 minutes.')
				UserLog.objects.create(user_id=user.id,
				                       ip=get_client_ip(request),
				                       action='Forgot password request',
				                       device=request.META['HTTP_USER_AGENT'])

				msg = {'data': 'We have sent a verification code to your phone, please verify.'}
				return Response(msg, status=status.HTTP_200_OK)

			else:
				return Response({'error': 'Unable to locate your account'}, status=status.HTTP_404_NOT_FOUND)
		elif request.method == 'POST':
			if not request.session.get('user_id'):
				return Response(status.HTTP_400_BAD_REQUEST)
			user = User.objects.get(id=request.session['user_id'])
			verification_code = user.verification_code
			# Check If code is valid
			if verification_code.is_expired:
				return Response({'error': 'Verification code expired, please request another code.'},
				                status=status.HTTP_400_BAD_REQUEST)
			if not (request.data.get('verification_code') == verification_code.code):
				return Response({'error': 'Verification code doesn\'t match, please try again or request another code.'},
				                status=status.HTTP_400_BAD_REQUEST)
			# Verification code is valid, so expire verification code
			verification_code.expire()
			request.session['change_password'] = True
			return Response(status=status.HTTP_200_OK)
		elif request.method == 'PATCH':
			# update password
			if not (request.session.get('change_password', False) and request.session.get('user_id', False)):
				return Response(status=status.HTTP_400_BAD_REQUEST)

			user = User.objects.get(id=request.session['user_id'])

			user.set_password(request.data['password'])
			user.save()
			# clear session
			del request.session['change_password']
			del request.session['user_id']
			UserLog.objects.create(user_id=user.id,
			                       ip=get_client_ip(request),
			                       action='Password changed',
			                       device=request.META['HTTP_USER_AGENT'])
			return Response(status=status.HTTP_200_OK)


class UserSignUpFollowUpViewSet(viewsets.ViewSet):
	"""
	The viewset for user sign up follow-up, includes phone verification, email verification and id uploading
	"""
	parser_classes = (MultiPartParser, FormParser, JSONParser)
	permission_classes = (IsAuthenticated,)

	def verify_email(self, request):
		# Verify user email
		investor_user = request.user.investor
		verification_code = request.user.verification_code
		if request.data.get('verification_code') == verification_code.code:
			if not verification_code.is_expired:
				# Update user verification level
				investor_user.verification_level = 0
				investor_user.save()

				# Expire verification code
				verification_code.expire()

				return Response(status=status.HTTP_200_OK)
			else:
				return Response({'error': 'Verification code expired, please request another code.'},
				                status=status.HTTP_400_BAD_REQUEST)
		else:
			return Response({'error': 'Verification code doesn\'t match, please try again or request another code.'},
			                status=status.HTTP_400_BAD_REQUEST)

	def verify_phone(self, request):
		# Add phone number for the current user and send verification code
		if request.method == 'POST':
			# request.data must contain country_name, phone
			country_name = request.data.get('country_name')
			if country_utils.is_valid_country(country_name):
				# Cache
				user = request.user
				investor_user = request.user.investor
				verification_code = request.user.verification_code

				# Update phone number of user model
				user.phone_country_code = country_utils.get_phone_prefix_by_country_name(country_name)
				user.phone = request.data.get('phone')
				try:
					user.save()
				except IntegrityError:
					return Response({'error': 'A user with this phone number already exists.'},
					                status=status.HTTP_403_FORBIDDEN)

				# Do an arbitrary assumption of user's nationality based on phone number
				investor_user.nationality = country_name
				investor_user.save()

				# Send SMS to user
				verification_code.refresh()
				phone_num = user.phone_country_code + user.phone
				msg = 'Verification Code: ' + verification_code.code + '\nInvalid in 5 minutes.'
				send_sms(phone_num, msg)

				return Response(status=status.HTTP_200_OK)
			else:
				return Response({'error': 'Phone number invalid, please check again'},
				                status=status.HTTP_400_BAD_REQUEST)

		# Verify user phone number
		elif request.method == 'PATCH':
			investor_user = request.user.investor
			verification_code = request.user.verification_code
			if request.data.get('verification_code') == verification_code.code:
				if not verification_code.is_expired:
					# Update user verification level
					investor_user.verification_level = 1
					investor_user.save()

					# Expire verification code
					verification_code.expire()

					return Response(status=status.HTTP_200_OK)
				else:
					return Response({'error': 'Verification code expired, please request another code.'},
					                status=status.HTTP_400_BAD_REQUEST)
			else:
				return Response({'error': 'Verification code doesn\'t match, please try again or request another code.'},
				                status=status.HTTP_400_BAD_REQUEST)

	def save_wallet_address(self, request):
		investor = request.user.investor
		if investor.wallet.eth_address and investor.verification_level == 2:
			return Response({'error': 'Your are already bound with a wallet'}, status=status.HTTP_403_FORBIDDEN)
		else:
			investor.wallet.eth_address = request.data.get('eth_address')
			investor.wallet.save()
			# Update verification level
			investor.verification_level = 2
			investor.save()
			return Response(status=status.HTTP_200_OK)


class UserViewSet(viewsets.ViewSet):
	parser_classes = (MultiPartParser, FormParser, JSONParser)
	permission_classes = (IsAuthenticated,)

	def me(self, request):
		if request.method == 'GET':
			# if request.user.is_investor:
			# 	serializer = FullInvestorUserSerializer(request.user.investor)
			# elif request.user.is_company_user:
			# 	# TODO
			# 	pass
			# elif request.user.is_analyst:
			# 	# TODO
			# 	pass

			# Retrieve self
			if request.user.is_investor:
				serializer = FullInvestorUserSerializer(request.user.investor)
			elif request.user.is_company_user:
				serializer = FullCompanyUserSerializer(request.user.company_user)

			return Response(serializer.data)
		elif request.method == 'PATCH':
			# Return error message if user is not investor
			if not request.user.is_investor:
				return Response(status.HTTP_403_FORBIDDEN)

			# Update Address
			if request.data.get('update') == 'address':
				# Check content
				if request.user.investor.address.first():
					address = request.user.investor.address.first()
					address.address1 = request.data['address1']
					address.address2 = request.data['address2']
					address.city = request.data['city']
					address.state = request.data['state']
					address.zipcode = request.data['zipcode']
					address.country = request.data['country']
					address.save()
				else:
					InvestorUserAddress.objects.create(investor_user_id=request.user.investor.id,
					                                   address1=request.data['address1'],
					                                   address2=request.data['address2'],
					                                   city=request.data['city'],
					                                   state=request.data['state'],
					                                   zipcode=request.data['zipcode'],
					                                   country=request.data['country'], )
				serializer = FullInvestorUserSerializer(request.user.investor)
				return Response(serializer.data, status=status.HTTP_200_OK)

			# Update Birthday
			elif request.data.get('update') == 'name_birthday':
				investor_user = request.user.investor

				# User cannot change birthday, name and nationality if user is being processed or verified
				if investor_user.verification_level > 2:
					return Response(status.HTTP_403_FORBIDDEN)

				if request.data.get('birthday'):
					investor_user.birthday = request.data.get('birthday')
				if request.data.get('first_name'):
					request.user.first_name = request.data.get('first_name')
				if request.data.get('last_name'):
					request.user.last_name = request.data.get('last_name')
				if request.data.get('nationality'):
					investor_user.nationality = request.data.get('nationality')
				investor_user.save()

				serializer = FullInvestorUserSerializer(request.user.investor)
				return Response(serializer.data, status=status.HTTP_200_OK)

	def send_verification_code(self, request):
		if request.data.get('email'):
			verification_code = request.user.verification_code
			verification_code.refresh()
			ctx = {
				# TODO: Potential Bug. Need to test.
				'user_full_name'   : request.user.investor.full_name if request.user.investor else request.user.company_user.__str__(),
				'verification_code': verification_code.code,
				'user_email'       : request.user.email
			}
			send_email([request.user.email], 'Gullin - Verification Code', 'verification_code', ctx)
			return Response(status=status.HTTP_200_OK)

		elif request.data.get('sms'):
			verification_code = request.user.verification_code
			verification_code.refresh()

			phone_num = request.user.phone_country_code + request.user.phone
			msg = 'Gullin Verification Code: ' + verification_code.code + '\n Valid in 5 minutes.'
			send_sms(phone_num, msg)

			return Response(status=status.HTTP_200_OK)

	def id_verification(self, request):
		# Copy the form data
		form_data = request.data.copy()
		investor = request.user.investor
		investor_address = investor.address.first()

		# # recreate id_front_file file by decoding base64
		# if request.data['official_id_front']:
		# 	form_data['official_id_front_base64'] = request.data['official_id_front']
		# 	# img_format, img_str = form_data['official_id_front'].split(';base64,')
		# 	# img_ext = img_format.split('/')[-1]
		# 	# id_front_file = ContentFile(base64.b64decode(img_str), name='front.' + img_ext)
		# 	# form_data['official_id_front'] = id_front_file
		#
		# # recreate id_back_file file by decoding base64
		# if request.data['official_id_back']:
		# 	form_data['official_id_back_base64'] = request.data['official_id_back']
		# 	# img_format, img_str = form_data['official_id_back'].split(';base64,')
		# 	# img_ext = img_format.split('/')[-1]
		# 	# id_back_file = ContentFile(base64.b64decode(img_str), name='back.' + img_ext)
		# 	# form_data['official_id_back'] = id_back_file
		#
		# # recreate id_holding_file file by decoding base64
		# if request.data['user_holding_official_id']:
		# 	form_data['user_holding_official_id_base64'] = request.data['user_holding_official_id']
		# 	# img_format, img_str = form_data['user_holding_official_id'].split(';base64,')
		# 	# img_ext = img_format.split('/')[-1]
		# 	# id_holding_file = ContentFile(base64.b64decode(img_str), name='hold.' + img_ext)
		# 	# form_data['user_holding_official_id'] = id_holding_file

		# Check if user already has id verification
		id_verification = IDVerification.objects.filter(investor_user_id=investor.id).first()
		# If has
		if id_verification:
			# Update it
			serializer = FullIDVerificationSerializer(id_verification, data=form_data, partial=True)
			if serializer.is_valid(raise_exception=True):
				id_verification = serializer.save()
			else:
				return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
		else:
			# Else create a new one
			serializer = FullIDVerificationSerializer(data=form_data)
			if serializer.is_valid(raise_exception=True):
				id_verification = serializer.save()
			else:
				return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

		# Form data for stage 1 checking
		form_data = {
			'man'  : request.user.email,
			'tea'  : request.user.email,

			'bfn'  : investor.first_name,
			'bln'  : investor.last_name,
			'dob'  : investor.birthday.isoformat(),

			'bsn'  : investor_address.address1 + ', ' + investor_address.address2 if investor_address.address2 else '',
			'bc'   : investor_address.city,
			'bs'   : investor_address.state,
			'bz'   : investor_address.zipcode,
			'bco'  : country_utils.get_ISO3166_code_by_country_name(investor_address.country),

			'ip'   : request.user.last_login_ip,
			'phn'  : request.user.phone_country_code + request.user.phone,

			'stage': 1,
		}
		# Send request
		res = requests.request('POST', settings.IDENTITY_MIND_API, auth=('gullin', settings.IDENTITY_MIND_KEY), json=form_data)
		# Get response
		res = json.loads(res.text)

		# Save transaction id, response and stage
		id_verification.tid = res['tid']
		id_verification.stage = 1
		id_verification.state = res['state']
		id_verification.note = res
		id_verification.processed = False
		id_verification.save()

		# send notification email to user
		ctx = {
			'user_full_name': investor.full_name,
			'user_email'    : request.user.email
		}
		send_email([request.user.email], 'Gullin - ID Verification Request Received', 'kyc_processing', ctx)

		investor.verification_level = 3
		investor.save()
		return Response(status=status.HTTP_201_CREATED)

	def accredited_investor_verification(self, request):
		if request.user.investor.verification_level == 4 and request.user.investor.nationality == 'United States':
			# Send team email
			ctx = {
				'title'  : 'A user requested accredited investor verification',
				'content': 'User detail: https://api.gullin.io/juM8A43L9GZ7/users/investoruser/' + str(request.user.investor.id) + '/change/ \n' +
				           'Link to proceed: https://verifyinvestor.com/issuer/verification/investors'
			}
			send_email(['team@gullin.io'], 'A user requested accredited investor verification.', 'gullin_team_notification', ctx)
			# requests.request('POST', 'https://chat.googleapis.com/v1/spaces/AAAAENCScR0/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=9AB9VmXEKZXb-xaQutMBFp-iG-QV169GfaUsNLe7pGc%3D',
			#                  json={'text': })

			# Send user email
			ctx = {
				'user_full_name': request.user.investor.full_name,
				'user_email'    : request.user.email
			}
			send_email([request.user.email], 'Gullin - ID Verification Request Received', 'aiv_processing', ctx)

			request.user.investor.verification_level = 5
			request.user.investor.save()

			return Response(status=status.HTTP_200_OK)
		else:
			return Response(status=status.HTTP_400_BAD_REQUEST)

	def log(self, request):
		# Return user log, the default page size is 50
		# Params:
		# 1. q, query_param, int
		page = request.query_params.get('p', 0)
		logs = request.user.logs.all()[page * 50:page * 50 + 50]
		serializer = FullUserLogVerificationSerializer(logs, many=True)
		return Response(serializer.data)

	def change_password(self, request):
		# If current_password or new_password not in request form
		if (not request.data['current_password']) or (not request.data['new_password']):
			# Return error message with status code 400
			return Response({'error': 'Form wrong format'}, status=status.HTTP_400_BAD_REQUEST)
		try:
			#  if old-password match
			if check_password(request.data['current_password'], request.user.password):
				# change user password
				request.user.set_password(request.data['new_password'])
				request.user.save()
				return Response(status=status.HTTP_200_OK)
			else:
				# else return with error message and status code 400
				return Response({'error': 'Current password not match'}, status=status.HTTP_400_BAD_REQUEST)
		except:
			# If exception return with status 400
			return Response({'error': 'Failed to update password'}, status=status.HTTP_400_BAD_REQUEST)

# # TODO delete
# @api_view(['GET'])
# def send_kyc_email(request, type, email):
# 	if type == 'success':
# 		user = User.objects.filter(email=email)
# 		if user:
# 			user = user[0]
# 			ctx = {
# 				'user_full_name': user.investor.full_name,
# 				'user_email'    : user.email
# 			}
# 			send_email([user.email], 'Gullin - ID Verification Approved', 'kyc_success', ctx)
# 			return Response({'data': 'email send'}, status=status.HTTP_200_OK)
# 		else:
# 			return Response({'data': 'user invalid'}, status=status.HTTP_200_OK)
#
# 	elif type == 'failed':
# 		user = User.objects.filter(email=email)
# 		if user:
# 			user = user[0]
# 			ctx = {
# 				'user_full_name': user.investor.full_name,
# 				'user_email'    : user.email
# 			}
# 			send_email([user.email], 'Gullin - ID Verification Rejected', 'kyc_failed', ctx)
# 			return Response({'data': 'email send'}, status=status.HTTP_200_OK)
# 		else:
# 			return Response({'data': 'user invalid'}, status=status.HTTP_200_OK)
#
# 	else:
# 		return Response({'data': 'parameter invalid'}, status=status.HTTP_200_OK)
