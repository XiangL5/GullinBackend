import random
import string
from datetime import timedelta
from storages.backends.s3boto3 import S3Boto3Storage

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager

from Gullin.utils.upload_dir import user_avatar_dir, official_id_dir


class UserManager(BaseUserManager):
	use_in_migrations = True

	def _create_user(self, email, password, **extra_fields):
		"""
		Create and save a user with the given username, email, and password.
		"""
		if not email:
			raise ValueError('The given username must be set')

		email = self.normalize_email(email)
		user = self.model(email=email, **extra_fields)
		user.set_password(password)
		user.save(using=self._db)
		return user

	def create_user(self, email=None, password=None, **extra_fields):
		extra_fields.setdefault('is_staff', False)
		extra_fields.setdefault('is_superuser', False)
		return self._create_user(email, password, **extra_fields)

	def create_superuser(self, email, password, **extra_fields):
		extra_fields.setdefault('is_staff', True)
		extra_fields.setdefault('is_superuser', True)

		if extra_fields.get('is_staff') is not True:
			raise ValueError('Superuser must have is_staff=True.')
		if extra_fields.get('is_superuser') is not True:
			raise ValueError('Superuser must have is_superuser=True.')

		return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
	"""
	Basic Users Model.
	For User Authentication
	"""

	# User Login
	email = models.EmailField(unique=True, blank=True,
	                          error_messages={'unique': "A user with that email already exists."})
	phone_country_code = models.CharField(max_length=30, null=True, blank=True)
	phone = models.CharField(max_length=30, null=True, blank=True)

	# Reference
	refer_source = models.CharField(max_length=30, null=True, blank=True)

	# Security
	last_login = models.DateTimeField(default=timezone.now)
	last_login_ip = models.GenericIPAddressField(null=True, blank=True)
	TOTP_enabled = models.BooleanField(default=False)

	# User Extension
	investor = models.OneToOneField('InvestorUser', related_name='user', on_delete=models.PROTECT, null=True, blank=True)
	analyst = models.OneToOneField('AnalystUser', related_name='user', on_delete=models.PROTECT, null=True, blank=True)
	company_user = models.OneToOneField('CompanyUser', related_name='user', on_delete=models.PROTECT, null=True, blank=True)

	# Permissions
	is_investor = models.BooleanField(
		default=True,
		help_text='Designates whether this user is investor.'
	)
	is_company_user = models.BooleanField(
		default=False,
		help_text='Designates whether this user is company.'
	)
	is_analyst = models.BooleanField(
		default=False,
		help_text='Designates whether this user is analyst.'
	)
	is_staff = models.BooleanField(
		default=False,
		help_text='Designates whether the user can log into this admin site.'
	)
	is_active = models.BooleanField(
		default=True,
		help_text='Designates whether this user should be treated as active. '
		          'Unselect this instead of deleting accounts.'
	)

	# TimeStamp
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)

	# Settings
	USERNAME_FIELD = 'email'
	objects = UserManager()

	class Meta:
		verbose_name_plural = '1. Users'
		ordering = ['-created']
		unique_together = ('phone_country_code', 'phone')

	def __str__(self):
		return self.email

	def update_last_login(self):
		self.last_login = timezone.now()
		self.save(update_fields=['last_login'])

	def update_last_login_ip(self, ip):
		self.last_login_ip = ip
		self.save(update_fields=['last_login_ip'])


class InvestorUser(models.Model):
	"""
	Investor Users are able to invest in ICOs, trade ICO Tokens.
	All users registered from frontend should be investor users.
	"""
	LEVEL_CHOICES = (
		(-1, 'Not Verified'),  # Not Verified
		(0, 'LEVEL 0 - Email Verified'),
		(1, 'LEVEL 1 - Phone Verified'),
		(2, 'LEVEL 2 - Wallet Created'),
		(3, 'LEVEL 3 - ID Processing'),
		(4, 'LEVEL 4 - ID Verified'),
		(5, 'LEVEL 5 - Accredited Investor Processing'),
		(6, 'LEVEL 6 - Accredited Investor Verified'),
	)

	# Personal Details
	first_name = models.CharField(max_length=30, null=True, blank=True)
	last_name = models.CharField(max_length=50, null=True, blank=True)
	nationality = models.CharField(max_length=20, null=True, blank=True)
	birthday = models.DateField(null=True, blank=True)

	# Verification
	verification_level = models.IntegerField(choices=LEVEL_CHOICES, default=-1)

	# TimeStamp
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)

	class Meta:
		verbose_name_plural = '2. Investor Users'

	def __str__(self):
		return self.full_name

	@property
	def full_name(self):
		return '{0} {1}'.format(self.first_name, self.last_name)


class CompanyUser(models.Model):
	"""
	Company Users are able to upload press releases, check company profile.
	Company Users can only be added by site admins.
	"""

	# Link to Company Model
	company = models.OneToOneField('companies.Company', related_name='user', on_delete=models.PROTECT, null=True)

	# TimeStamp
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)

	class Meta:
		verbose_name_plural = '3. Company Users'

	def __str__(self):
		return self.company.name + ' Admin'


class AnalystUser(models.Model):
	"""
	Analyst Users are able to submit analyses to ICOs or companies .
	Analyst Users can only be added by site admins.
	"""
	ANALYST_TYPE_CHOICES = (
		(0, 'Professional'),
		(1, 'Regular')
	)

	# Personal Info
	avatar = models.ImageField(upload_to=user_avatar_dir, default='avatars/default.jpg', null=True, blank=True)
	first_name = models.CharField(max_length=30, null=True, blank=True)
	last_name = models.CharField(max_length=50, null=True, blank=True)

	# Analyst Info
	analyst_type = models.IntegerField(choices=ANALYST_TYPE_CHOICES, default=1)

	# TimeStamp
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)

	class Meta:
		verbose_name = 'Analyst'
		verbose_name_plural = 'Subusers - Analyst'

	def __str__(self):
		return self.full_name

	@property
	def full_name(self):
		return self.first_name + ' ' + self.last_name


class InvestorUserAddress(models.Model):
	"""
	InvestorUserAddress model is used for store InvestorUser address.
	"""
	# Investor user
	investor_user = models.ForeignKey('InvestorUser', related_name='address', on_delete=models.CASCADE)

	# Address Info
	address1 = models.CharField(max_length=400)
	address2 = models.CharField(max_length=200, null=True, blank=True)
	city = models.CharField(max_length=200)
	state = models.CharField(max_length=200)
	zipcode = models.CharField(max_length=200)
	country = models.CharField(max_length=200)

	# TimeStamp
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)

	class Meta:
		verbose_name_plural = '4. Investor User Address'

	def __str__(self):
		return 'Investor Address'


class IDVerification(models.Model):
	"""
	ID Verification model is used for verify InvestorUser identity.
	"""

	ID_TYPE_CHOICES = (('DL', 'Driver License'),
	                   ('ID', 'Photo ID'),
	                   ('PP', 'Passport'))
	ID_VERIFICATION_STATE = (('A', 'Accepted'),
	                         ('R', 'Under Review'),
	                         ('D', 'Rejected'),)

	investor_user = models.OneToOneField('InvestorUser', related_name='id_verification', on_delete=models.CASCADE, null=True, blank=True)

	# Verification Info
	official_id_type = models.CharField(max_length=20, choices=ID_TYPE_CHOICES)
	# File
	# official_id_front = models.FileField(upload_to=official_id_dir, storage=S3Boto3Storage(bucket='gullin-id-verification'))
	# official_id_back = models.FileField(upload_to=official_id_dir, null=True, blank=True, storage=S3Boto3Storage(bucket='gullin-id-verification'))
	# user_holding_official_id = models.FileField(upload_to=official_id_dir, storage=S3Boto3Storage(bucket='gullin-id-verification'))

	# Base64 Cache
	official_id_front_base64 = models.TextField(null=True, blank=True)
	official_id_back_base64 = models.TextField(null=True, blank=True)
	user_holding_official_id_base64 = models.TextField(null=True, blank=True)

	# Transaction Detail
	tid = models.CharField(max_length=40, null=True, blank=True)
	stage = models.IntegerField(default=0)
	state = models.CharField(choices=ID_VERIFICATION_STATE, max_length=10, null=True, blank=True)
	processed = models.BooleanField(default=False)

	# Note
	note = models.TextField(null=True, blank=True)

	# TimeStamp
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)

	class Meta:
		verbose_name_plural = '5. ID Verifications'

	def __str__(self):
		return self.official_id_type


class InvestorVerification(models.Model):
	"""
	Investor Verification is for Accredited Investor Verification for US based InvestorUsers
	"""

	DOC_CHOICES = (('Tax Return', 'Tax Return'),
	               ('Bank Statement', 'Bank Statement'))

	investor_user = models.OneToOneField('InvestorUser', related_name='accredited_investor_verification', on_delete=models.CASCADE, null=True, blank=True)

	doc_type = models.CharField(max_length=20, choices=DOC_CHOICES)
	doc1 = models.FileField(upload_to=official_id_dir, null=True, blank=True, storage=S3Boto3Storage(bucket='gullin-id-verification'))
	doc2 = models.FileField(upload_to=official_id_dir, null=True, blank=True, storage=S3Boto3Storage(bucket='gullin-id-verification'))

	class Meta:
		verbose_name_plural = '6. Accredited Investor Verifications'

	def __str__(self):
		return self.doc_type


class VerificationCode(models.Model):
	"""
	Verification Code model
	1. For verify user email
	2. For verify user phone number
	3. For 2 factor verification (not TOTP enabled users only, if user enabled TOTP, TOTP generated code should be used instead)
	"""

	user = models.OneToOneField('User', related_name='verification_code', on_delete=models.PROTECT)
	code = models.CharField(max_length=200)
	expire_time = models.DateTimeField(default=timezone.now)

	class Meta:
		verbose_name_plural = '7. Verification Codes'

	@property
	def is_expired(self):
		return timezone.now() > self.expire_time

	def expire(self):
		self.expire_time = timezone.now()
		self.save()

	def refresh(self):
		self.code = ''.join([random.choice(string.digits) for n in range(6)])
		self.expire_time = timezone.now() + timedelta(minutes=5)
		self.save()


class UserLog(models.Model):
	"""
	UserLog Code model
	"""
	user = models.ForeignKey('User', related_name='logs', on_delete=models.CASCADE)
	action = models.CharField(max_length=200)
	ip = models.GenericIPAddressField()
	device = models.CharField(max_length=200)
	datetime = models.DateTimeField(auto_now_add=True)

	class Meta:
		verbose_name_plural = '8. User Logs'
		ordering = ['-datetime']

	def __str__(self):
		return 'UserLog ' + self.datetime.isoformat()


# Signal handling function to add VerificationCode to every new created User instance
@receiver(post_save, sender=User)
def add_verification_code_to_user(sender, **kwargs):
	if kwargs.get('created', True):
		VerificationCode.objects.create(user=kwargs.get('instance'))

# # Signal handling function to send email to user when user create new kyc application
# @receiver(post_save, sender=IDVerification)
# def id_verification_processing_email(sender, **kwargs):
# 	if kwargs.get('created', True):
# 		id_verification = kwargs.get('instance')
# 		user = id_verification.investor_user.user
# 		ctx = {
# 			'user_full_name': user.investor.full_name,
# 			'user_email'    : user.email
# 		}
# 		send_email([user.email], 'Gullin - ID Verification Request Received', 'kyc_processing', ctx)
