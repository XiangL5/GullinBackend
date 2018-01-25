def is_valid_country(country_name):
	data = ['Bangladesh', 'Belgium', 'Burkina Faso', 'Bulgaria', 'Bosnia and Herzegovina', 'Barbados', 'Wallis and Futuna', 'Saint Barthelemy', 'Bermuda', 'Brunei', 'Bolivia', 'Bahrain', 'Burundi',
	        'Benin',
	        'Bhutan', 'Jamaica', 'Bouvet Island', 'Botswana', 'Samoa', 'Bonaire, Saint Eustatius and Saba ', 'Brazil', 'Bahamas', 'Jersey', 'Belarus', 'Belize', 'Russia', 'Rwanda', 'Serbia',
	        'East Timor',
	        'Reunion', 'Turkmenistan', 'Tajikistan', 'Romania', 'Tokelau', 'Guinea-Bissau', 'Guam', 'Guatemala', 'South Georgia and the South Sandwich Islands', 'Greece', 'Equatorial Guinea',
	        'Guadeloupe',
	        'Japan', 'Guyana', 'Guernsey', 'French Guiana', 'Georgia', 'Grenada', 'United Kingdom', 'Gabon', 'El Salvador', 'Guinea', 'Gambia', 'Greenland', 'Gibraltar', 'Ghana', 'Oman', 'Tunisia',
	        'Jordan',
	        'Croatia', 'Haiti', 'Hungary', 'Hong Kong', 'Honduras', 'Heard Island and McDonald Islands', 'Venezuela', 'Palestinian Territory', 'Palau', 'Portugal', 'Svalbard and Jan Mayen',
	        'Paraguay', 'Iraq',
	        'Panama', 'French Polynesia', 'Papua New Guinea', 'Peru', 'Pakistan', 'Philippines', 'Pitcairn', 'Poland', 'Saint Pierre and Miquelon', 'Zambia', 'Western Sahara', 'Estonia', 'Egypt',
	        'South Africa',
	        'Ecuador', 'Italy', 'Vietnam', 'Solomon Islands', 'Ethiopia', 'Somalia', 'Zimbabwe', 'Saudi Arabia', 'Spain', 'Eritrea', 'Montenegro', 'Moldova', 'Madagascar', 'Saint Martin', 'Morocco',
	        'Monaco',
	        'Uzbekistan', 'Myanmar', 'Mali', 'Macao', 'Mongolia', 'Marshall Islands', 'Macedonia', 'Mauritius', 'Malta', 'Malawi', 'Maldives', 'Martinique', 'Northern Mariana Islands', 'Montserrat',
	        'Mauritania', 'Isle of Man', 'Uganda', 'Tanzania', 'Malaysia', 'Mexico', 'Israel', 'France', 'British Indian Ocean Territory', 'Saint Helena', 'Finland', 'Fiji', 'Falkland Islands',
	        'Micronesia',
	        'Faroe Islands', 'Nicaragua', 'Netherlands', 'Norway', 'Namibia', 'Vanuatu', 'New Caledonia', 'Niger', 'Norfolk Island', 'Nigeria', 'New Zealand', 'Nepal', 'Nauru', 'Niue', 'Cook Islands',
	        'Kosovo',
	        'Ivory Coast', 'Switzerland', 'Colombia', 'China', 'Cameroon', 'Chile', 'Cocos Islands', 'Canada', 'Republic of the Congo', 'Central African Republic', 'Democratic Republic of the Congo',
	        'Czech Republic', 'Cyprus', 'Christmas Island', 'Costa Rica', 'Curacao', 'Cape Verde', 'Cuba', 'Swaziland', 'Syria', 'Sint Maarten', 'Kyrgyzstan', 'Kenya', 'South Sudan', 'Suriname',
	        'Kiribati',
	        'Cambodia', 'Saint Kitts and Nevis', 'Comoros', 'Sao Tome and Principe', 'Slovakia', 'South Korea', 'Slovenia', 'North Korea', 'Kuwait', 'Senegal', 'San Marino', 'Sierra Leone',
	        'Seychelles',
	        'Kazakhstan', 'Cayman Islands', 'Singapore', 'Sweden', 'Sudan', 'Dominican Republic', 'Dominica', 'Djibouti', 'Denmark', 'British Virgin Islands', 'Germany', 'Yemen', 'Algeria',
	        'United States',
	        'Uruguay', 'Mayotte', 'United States Minor Outlying Islands', 'Lebanon', 'Saint Lucia', 'Laos', 'Tuvalu', 'Taiwan', 'Trinidad and Tobago', 'Turkey', 'Sri Lanka', 'Liechtenstein', 'Latvia',
	        'Tonga',
	        'Lithuania', 'Luxembourg', 'Liberia', 'Lesotho', 'Thailand', 'French Southern Territories', 'Togo', 'Chad', 'Turks and Caicos Islands', 'Libya', 'Vatican',
	        'Saint Vincent and the Grenadines',
	        'United Arab Emirates', 'Andorra', 'Antigua and Barbuda', 'Afghanistan', 'Anguilla', 'Iceland', 'Iran', 'Armenia', 'Albania', 'Angola', 'Antarctica', 'American Samoa', 'Argentina',
	        'Australia',
	        'Austria', 'Aruba', 'India', 'Aland Islands', 'Azerbaijan', 'Ireland', 'Indonesia', 'Ukraine', 'Qatar', 'Mozambique']
	if country_name in data:
		return True
	else:
		return False

def get_code_by_country_name(country_name):
	data = {'Bangladesh'              : '+880', 'Belgium': '+32', 'Burkina Faso': '+226', 'Bulgaria': '+359', 'Bosnia and Herzegovina': '+387', 'Barbados': '+1', 'Wallis and Futuna': '+681',
	        'Saint Barthelemy'        : '+590', 'Bermuda': '+1', 'Brunei': '+673', 'Bolivia': '+591', 'Bahrain': '+973', 'Burundi': '+257', 'Benin': '+229', 'Bhutan': '+975', 'Jamaica': '+1',
	        'Bouvet Island'           : '+55', 'Botswana': '+267', 'Samoa': '+685', 'Bonaire, Saint Eustatius and Saba ': '+599', 'Brazil': '+55', 'Bahamas': '+1', 'Jersey': '+44', 'Belarus': '+375',
	        'Belize'                  : '+501', 'Russia': '+7', 'Rwanda': '+250', 'Serbia': '+381', 'East Timor': '+670', 'Reunion': '+262', 'Turkmenistan': '+993', 'Tajikistan': '+992',
	        'Romania'                 : '+40',
	        'Tokelau'                 : '+690', 'Guinea-Bissau': '+245', 'Guam': '+1', 'Guatemala': '+502', 'South Georgia and the South Sandwich Islands': '+', 'Greece': '+30',
	        'Equatorial Guinea'       : '+240',
	        'Guadeloupe'              : '+590', 'Japan': '+81', 'Guyana': '+592', 'Guernsey': '+44-', 'French Guiana': '+594', 'Georgia': '+995', 'Grenada': '+1', 'United Kingdom': '+44',
	        'Gabon'                   : '+241',
	        'El Salvador'             : '+503', 'Guinea': '+224', 'Gambia': '+220', 'Greenland': '+299', 'Gibraltar': '+350', 'Ghana': '+233', 'Oman': '+968', 'Tunisia': '+216', 'Jordan': '+962',
	        'Croatia'                 : '+385',
	        'Haiti'                   : '+509', 'Hungary': '+36', 'Hong Kong': '+852', 'Honduras': '+504', 'Heard Island and McDonald Islands': '+ ', 'Venezuela': '+58',
	        'Palestinian Territory'   : '+970', 'Palau': '+680', 'Portugal': '+351', 'Svalbard and Jan Mayen': '+47', 'Paraguay': '+595', 'Iraq': '+964', 'Panama': '+507', 'French Polynesia': '+689',
	        'Papua New Guinea'        : '+675', 'Peru': '+51', 'Pakistan': '+92', 'Philippines': '+63', 'Pitcairn': '+870', 'Poland': '+48', 'Saint Pierre and Miquelon': '+508', 'Zambia': '+260',
	        'Western Sahara'          : '+212', 'Estonia': '+372', 'Egypt': '+20', 'South Africa': '+27', 'Ecuador': '+593', 'Italy': '+39', 'Vietnam': '+84', 'Solomon Islands': '+677',
	        'Ethiopia'                : '+251',
	        'Somalia'                 : '+252', 'Zimbabwe': '+263', 'Saudi Arabia': '+966', 'Spain': '+34', 'Eritrea': '+291', 'Montenegro': '+382', 'Moldova': '+373', 'Madagascar': '+261',
	        'Saint Martin'            : '+590',
	        'Morocco'                 : '+212', 'Monaco': '+377', 'Uzbekistan': '+998', 'Myanmar': '+95', 'Mali': '+223', 'Macao': '+853', 'Mongolia': '+976', 'Marshall Islands': '+692',
	        'Macedonia'               : '+389',
	        'Mauritius'               : '+230', 'Malta': '+356', 'Malawi': '+265', 'Maldives': '+960', 'Martinique': '+596', 'Northern Mariana Islands': '+1', 'Montserrat': '+1', 'Mauritania': '+222',
	        'Isle of Man'             : '+44', 'Uganda': '+256', 'Tanzania': '+255', 'Malaysia': '+60', 'Mexico': '+52', 'Israel': '+972', 'France': '+33', 'British Indian Ocean Territory': '+246',
	        'Saint Helena'            : '+290', 'Finland': '+358', 'Fiji': '+679', 'Falkland Islands': '+500', 'Micronesia': '+691', 'Faroe Islands': '+298', 'Nicaragua': '+505', 'Netherlands': '+31',
	        'Norway'                  : '+47', 'Namibia': '+264 ', 'Vanuatu': '+678', 'New Caledonia': '+687', 'Niger': '+227', 'Norfolk Island': '+672', 'Nigeria': '+234', 'New Zealand': '+64',
	        'Nepal'                   : '+977',
	        'Nauru'                   : '+674', 'Niue': '+683', 'Cook Islands': '+682', 'Kosovo': '+', 'Ivory Coast': '+225', 'Switzerland': '+41', 'Colombia': '+57', 'China': '+86',
	        'Cameroon'                : '+237',
	        'Chile'                   : '+56', 'Cocos Islands': '+61', 'Canada': '+1', 'Republic of the Congo': '+242', 'Central African Republic': '+236', 'Democratic Republic of the Congo': '+243',
	        'Czech Republic'          : '+420', 'Cyprus': '+357', 'Christmas Island': '+61', 'Costa Rica': '+506', 'Curacao': '+599', 'Cape Verde': '+238', 'Cuba': '+53', 'Swaziland': '+268',
	        'Syria'                   : '+963',
	        'Sint Maarten'            : '+599', 'Kyrgyzstan': '+996', 'Kenya': '+254', 'South Sudan': '+211', 'Suriname': '+597', 'Kiribati': '+686', 'Cambodia': '+855', 'Saint Kitts and Nevis': '+1',
	        'Comoros'                 : '+269', 'Sao Tome and Principe': '+239', 'Slovakia': '+421', 'South Korea': '+82', 'Slovenia': '+386', 'North Korea': '+850', 'Kuwait': '+965',
	        'Senegal'                 : '+221',
	        'San Marino'              : '+378', 'Sierra Leone': '+232', 'Seychelles': '+248', 'Kazakhstan': '+7', 'Cayman Islands': '+1', 'Singapore': '+65', 'Sweden': '+46', 'Sudan': '+249',
	        'Dominican Republic'      : '+1', 'Dominica': '+1', 'Djibouti': '+253', 'Denmark': '+45', 'British Virgin Islands': '+1', 'Germany': '+49', 'Yemen': '+967', 'Algeria': '+213',
	        'United States'           : '+1', 'Uruguay': '+598', 'Mayotte': '+262', 'United States Minor Outlying Islands': '+1', 'Lebanon': '+961', 'Saint Lucia': '+1', 'Laos': '+856',
	        'Tuvalu'                  : '+688',
	        'Taiwan'                  : '+886', 'Trinidad and Tobago': '+1', 'Turkey': '+90', 'Sri Lanka': '+94', 'Liechtenstein': '+423', 'Latvia': '+371', 'Tonga': '+676', 'Lithuania': '+370',
	        'Luxembourg'              : '+352', 'Liberia': '+231', 'Lesotho': '+266', 'Thailand': '+66', 'French Southern Territories': '+', 'Togo': '+228', 'Chad': '+235',
	        'Turks and Caicos Islands': '+1',
	        'Libya'                   : '+218', 'Vatican': '+379', 'Saint Vincent and the Grenadines': '+1', 'United Arab Emirates': '+971', 'Andorra': '+376', 'Antigua and Barbuda': '+1',
	        'Afghanistan'             : '+93', 'Anguilla': '+1', 'Iceland': '+354', 'Iran': '+98', 'Armenia': '+374', 'Albania': '+355', 'Angola': '+244', 'Antarctica': '+',
	        'American Samoa'          : '+1', 'Argentina': '+54', 'Australia': '+61', 'Austria': '+43', 'Aruba': '+297', 'India': '+91', 'Aland Islands': '+358', 'Azerbaijan': '+994',
	        'Ireland'                 : '+353',
	        'Indonesia'               : '+62', 'Ukraine': '+380', 'Qatar': '+974', 'Mozambique': '+258'}
	try:
		return data[country_name]
	except KeyError:
		return None

