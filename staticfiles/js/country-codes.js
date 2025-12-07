// Country to phone code mapping - All 195 UN countries
const countryPhoneCodes = {
    'Afghanistan': '+93',
    'Albania': '+355',
    'Algeria': '+213',
    'Andorra': '+376',
    'Angola': '+244',
    'Antigua and Barbuda': '+1-268',
    'Argentina': '+54',
    'Armenia': '+374',
    'Australia': '+61',
    'Austria': '+43',
    'Azerbaijan': '+994',
    'Bahamas': '+1-242',
    'Bahrain': '+973',
    'Bangladesh': '+880',
    'Barbados': '+1-246',
    'Belarus': '+375',
    'Belgium': '+32',
    'Belize': '+501',
    'Benin': '+229',
    'Bhutan': '+975',
    'Bolivia': '+591',
    'Bosnia and Herzegovina': '+387',
    'Botswana': '+267',
    'Brazil': '+55',
    'Brunei': '+673',
    'Bulgaria': '+359',
    'Burkina Faso': '+226',
    'Burundi': '+257',
    'Cabo Verde': '+238',
    'Cambodia': '+855',
    'Cameroon': '+237',
    'Canada': '+1',
    'Central African Republic': '+236',
    'Chad': '+235',
    'Chile': '+56',
    'China': '+86',
    'Colombia': '+57',
    'Comoros': '+269',
    'Congo': '+242',
    'Costa Rica': '+506',
    'Croatia': '+385',
    'Cuba': '+53',
    'Cyprus': '+357',
    'Czech Republic': '+420',
    'Democratic Republic of the Congo': '+243',
    'Denmark': '+45',
    'Djibouti': '+253',
    'Dominica': '+1-767',
    'Dominican Republic': '+1-809',
    'East Timor': '+670',
    'Ecuador': '+593',
    'Egypt': '+20',
    'El Salvador': '+503',
    'Equatorial Guinea': '+240',
    'Eritrea': '+291',
    'Estonia': '+372',
    'Eswatini': '+268',
    'Ethiopia': '+251',
    'Fiji': '+679',
    'Finland': '+358',
    'France': '+33',
    'Gabon': '+241',
    'Gambia': '+220',
    'Georgia': '+995',
    'Germany': '+49',
    'Ghana': '+233',
    'Greece': '+30',
    'Grenada': '+1-473',
    'Guatemala': '+502',
    'Guinea': '+224',
    'Guinea-Bissau': '+245',
    'Guyana': '+592',
    'Haiti': '+509',
    'Honduras': '+504',
    'Hungary': '+36',
    'Iceland': '+354',
    'India': '+91',
    'Indonesia': '+62',
    'Iran': '+98',
    'Iraq': '+964',
    'Ireland': '+353',
    'Israel': '+972',
    'Italy': '+39',
    'Ivory Coast': '+225',
    'Jamaica': '+1-876',
    'Japan': '+81',
    'Jordan': '+962',
    'Kazakhstan': '+7',
    'Kenya': '+254',
    'Kiribati': '+686',
    'Kuwait': '+965',
    'Kyrgyzstan': '+996',
    'Laos': '+856',
    'Latvia': '+371',
    'Lebanon': '+961',
    'Lesotho': '+266',
    'Liberia': '+231',
    'Libya': '+218',
    'Liechtenstein': '+423',
    'Lithuania': '+370',
    'Luxembourg': '+352',
    'Madagascar': '+261',
    'Malawi': '+265',
    'Malaysia': '+60',
    'Maldives': '+960',
    'Mali': '+223',
    'Malta': '+356',
    'Marshall Islands': '+692',
    'Mauritania': '+222',
    'Mauritius': '+230',
    'Mexico': '+52',
    'Micronesia': '+691',
    'Moldova': '+373',
    'Monaco': '+377',
    'Mongolia': '+976',
    'Montenegro': '+382',
    'Morocco': '+212',
    'Mozambique': '+258',
    'Myanmar': '+95',
    'Namibia': '+264',
    'Nauru': '+674',
    'Nepal': '+977',
    'Netherlands': '+31',
    'New Zealand': '+64',
    'Nicaragua': '+505',
    'Niger': '+227',
    'Nigeria': '+234',
    'North Korea': '+850',
    'North Macedonia': '+389',
    'Norway': '+47',
    'Oman': '+968',
    'Pakistan': '+92',
    'Palau': '+680',
    'Palestine': '+970',
    'Panama': '+507',
    'Papua New Guinea': '+675',
    'Paraguay': '+595',
    'Peru': '+51',
    'Philippines': '+63',
    'Poland': '+48',
    'Portugal': '+351',
    'Qatar': '+974',
    'Romania': '+40',
    'Russia': '+7',
    'Rwanda': '+250',
    'Saint Kitts and Nevis': '+1-869',
    'Saint Lucia': '+1-758',
    'Saint Vincent and the Grenadines': '+1-784',
    'Samoa': '+685',
    'San Marino': '+378',
    'Sao Tome and Principe': '+239',
    'Saudi Arabia': '+966',
    'Senegal': '+221',
    'Serbia': '+381',
    'Seychelles': '+248',
    'Sierra Leone': '+232',
    'Singapore': '+65',
    'Slovakia': '+421',
    'Slovenia': '+386',
    'Solomon Islands': '+677',
    'Somalia': '+252',
    'South Africa': '+27',
    'South Korea': '+82',
    'South Sudan': '+211',
    'Spain': '+34',
    'Sri Lanka': '+94',
    'Sudan': '+249',
    'Suriname': '+597',
    'Sweden': '+46',
    'Switzerland': '+41',
    'Syria': '+963',
    'Tajikistan': '+992',
    'Tanzania': '+255',
    'Thailand': '+66',
    'Togo': '+228',
    'Tonga': '+676',
    'Trinidad and Tobago': '+1-868',
    'Tunisia': '+216',
    'Turkey': '+90',
    'Turkmenistan': '+993',
    'Tuvalu': '+688',
    'Uganda': '+256',
    'Ukraine': '+380',
    'United Arab Emirates': '+971',
    'United Kingdom': '+44',
    'United States': '+1',
    'Uruguay': '+598',
    'Uzbekistan': '+998',
    'Vanuatu': '+678',
    'Vatican City': '+379',
    'Venezuela': '+58',
    'Vietnam': '+84',
    'Yemen': '+967',
    'Zambia': '+260',
    'Zimbabwe': '+263',
};

// Function to update phone field with country code
function updatePhoneCode() {
    console.log('updatePhoneCode called');
    
    const countrySelect = document.getElementById('id_country');
    const phoneInput = document.getElementById('id_phone');

    console.log('Country select element:', countrySelect);
    console.log('Phone input element:', phoneInput);

    if (!countrySelect || !phoneInput) {
        console.error('Country select or phone input not found!');
        return;
    }

    const selectedCountry = countrySelect.value;
    console.log('Selected country:', selectedCountry);
    
    const countryCode = countryPhoneCodes[selectedCountry];
    console.log('Country code:', countryCode);

    if (countryCode) {
        // Get current phone value
        let currentPhone = phoneInput.value.trim();
        console.log('Current phone value:', currentPhone);

        // Remove any existing country code
        Object.values(countryPhoneCodes).forEach(code => {
            if (currentPhone.startsWith(code)) {
                currentPhone = currentPhone.substring(code.length).trim();
            }
        });

        // Add new country code
        phoneInput.value = countryCode + ' ' + currentPhone;
        console.log('New phone value:', phoneInput.value);

        // Update placeholder
        phoneInput.placeholder = 'e.g., ' + countryCode + ' 123456789';
    } else {
        // Reset placeholder if no country selected
        phoneInput.placeholder = 'Enter phone number';
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded - Initializing country code auto-population');
    
    const countrySelect = document.getElementById('id_country');

    if (countrySelect) {
        console.log('Country select found, adding change event listener');
        
        // Add event listener for country change
        countrySelect.addEventListener('change', function() {
            console.log('Country changed event triggered');
            updatePhoneCode();
        });

        // Update phone code if country is already selected (e.g., on form validation error)
        if (countrySelect.value) {
            console.log('Country already selected on page load:', countrySelect.value);
            updatePhoneCode();
        }
    } else {
        console.error('Country select element not found with id: id_country');
    }
    
    const phoneInput = document.getElementById('id_phone');
    if (!phoneInput) {
        console.error('Phone input element not found with id: id_phone');
    }
});
