import random
import string
from datetime import timedelta

from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from django.contrib.auth.models import AbstractUser, PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager

from Gullin.utils.upload_dir import user_avatar_dir, official_id_dir
from Gullin.utils.send.sms import send_sms

from django.utils import timezone


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
	phone = models.CharField(max_length=30, unique=True, null=True, blank=True,
	                         error_messages={'unique': "A user with that phone already exists."})

	# Security
	last_login = models.DateTimeField(auto_now_add=True)
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
		verbose_name = 'Base User'
		verbose_name_plural = 'Base Users'
		ordering = ['-created']

	def __str__(self):
		return self.email

	def update_last_login(self):
		self.last_login = timezone.now()
		self.save(update_fields=['last_login'])

	def update_last_login_ip(self, ip):
		if self.last_login_ip and ip != self.last_login_ip:
			# TODO: Block User Login
			# TODO: Send email
			self.last_login_ip = ip

	def send_sms(self):
		send_sms(self.phone_country_code + self.phone, 'Test Msg')


class InvestorUser(models.Model):
	"""
	Investor Users are able to invest in ICOs, trade ICO Tokens.
	All users registered from frontend should be investor users.
	"""
	LEVEL_CHOICES = (
		(-1, 'Not Verified'),  # Not Verified
		(0, 'LEVEL 0'),  # Email Verified
		(1, 'LEVEL 1'),  # Phone Verified
		(2, 'LEVEL 2'),  # ID Verified US Citizen
		(3, 'LEVEL 3'),  # ID Verified non-US Citizen or Accredited Investor
	)

	avatar = models.ImageField(upload_to=user_avatar_dir, default='avatars/default.jpg', null=True, blank=True)
	first_name = models.CharField(max_length=30, null=True, blank=True)
	last_name = models.CharField(max_length=50, null=True, blank=True)
	nationality = models.CharField(max_length=20, null=True, blank=True)

	# Verification
	verification_level = models.IntegerField(choices=LEVEL_CHOICES, default=-1)
	id_verification = models.OneToOneField('IDVerification', related_name='investor_user', on_delete=models.PROTECT, null=True, blank=True)
	accredited_investor_verification = models.OneToOneField('InvestorVerification', related_name='investor_user', on_delete=models.PROTECT, null=True, blank=True)

	# TimeStamp
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)

	class Meta:
		verbose_name = 'Investor'
		verbose_name_plural = 'Subusers - Investor'

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
		verbose_name = 'Company User'
		verbose_name_plural = 'Subusers - Company User'

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


class IDVerification(models.Model):
	"""
	ID Verification model is used for verify InvestorUser identity.
	"""

	ID_TYPE_CHOICES = (('Driver License', 'Driver License'),
	                   ('Photo ID', 'Photo ID'),
	                   ('Passport', 'Passport'))
	# Verification Info
	official_id_type = models.CharField(max_length=20, choices=ID_TYPE_CHOICES)
	official_id_front = models.FileField(upload_to=official_id_dir, null=True, blank=True)
	official_id_back = models.FileField(upload_to=official_id_dir, null=True, blank=True)

	nationality = models.CharField(max_length=20, null=True, blank=True)

	# Identifier
	is_verified = models.BooleanField(default=False)

	# TimeStamp
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)

	class Meta:
		verbose_name = 'ID Verification'
		verbose_name_plural = 'User Verification - ID'

	def __str__(self):
		return self.official_id_type

	def verify_identity(self):
		# cache
		investor = self.investor_user
		# update verification status
		self.is_verified = True
		# sync nationality (this is for users who use different country phone number when register,
		# when we manually check user identity, we have to update user nationality on the admin portal and sync with investor user model)
		investor.nationality = self.nationality
		# update user verification level
		if self.nationality == 'United States':
			investor.verification_level = 2
		else:
			investor.verification_level = 3
		# save
		self.save()
		investor.save()

	# TODO: send email to user for the status updating

	def unverify_identity(self):
		# cache
		investor = self.investor_user
		# update verification status
		self.is_verified = True
		# update user verification level
		investor.verification_level = 1
		# save
		self.save()
		investor.save()
	# TODO: send email to user for the status updating


class InvestorVerification(models.Model):
	"""
	Investor Verification is for Accredited Investor Verification for US based InvestorUsers
	"""

	DOC_CHOICES = (('Tax Return', 'Tax Return'),
	               ('Bank Statement', 'Bank Statement'))

	doc_type = models.CharField(max_length=20, choices=DOC_CHOICES)
	doc1 = models.FileField(upload_to=official_id_dir, null=True, blank=True)
	doc2 = models.FileField(upload_to=official_id_dir, null=True, blank=True)

	class Meta:
		verbose_name = 'Accredited Investor Verification'
		verbose_name_plural = 'User Verification - Accredited Investor'

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
	expire_time = models.DateTimeField(default='django.utils.timezone.now')

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


# Signal handling function to add VerificationCode to every new created User instance
@receiver(post_save, sender=User)
def add_verification_code_to_user(sender, **kwargs):
	if kwargs.get('created', True):
		VerificationCode.objects.create(user=kwargs.get('instance'))
